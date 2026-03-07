CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Documents
CREATE TABLE public.documents (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  file_name text NOT NULL,
  bucket_path text NOT NULL,
  status text NOT NULL DEFAULT 'pending' 
    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  file_hash text NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- 2. Chunks 
CREATE TABLE public.chunks (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  document_id uuid NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
  content text NOT NULL,
  metadata jsonb,
  embedding vector(1024) NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- 3. Conversations
CREATE TABLE public.conversations (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  document_id uuid NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
  title text DEFAULT 'Untitled',
  created_at timestamptz DEFAULT now()
);

-- 4. Messages
CREATE TABLE public.messages (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- 5. Citations
CREATE TABLE public.citations (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  message_id uuid NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
  chunk_id uuid NOT NULL REFERENCES public.chunks(id) ON DELETE CASCADE,
  cited_text text NOT NULL,
  metadata jsonb,
  similarity_score float NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(message_id, chunk_id)
);

-- 6. Indexes
CREATE INDEX ON public.chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_document_id ON public.chunks(document_id);
CREATE INDEX idx_documents_user_id ON public.documents(user_id);
CREATE INDEX idx_documents_status ON public.documents(status) WHERE status != 'completed';
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX idx_conversations_document_id ON public.conversations(document_id);
CREATE INDEX idx_messages_conversation_id ON public.messages(conversation_id, created_at);
CREATE INDEX idx_citations_message_id ON public.citations(message_id);
CREATE INDEX idx_documents_user_hash ON public.documents(user_id, file_hash);

-- 7. Trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_documents_updated_at
  BEFORE UPDATE ON public.documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Enable RLS 
alter table public.documents enable row level security;
alter table public.chunks enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
ALTER TABLE public.citations ENABLE ROW LEVEL SECURITY;


-- Policies
create policy "Users can see own documents"
on public.documents for select
using (auth.uid() = user_id);

create policy "Users can insert own documents"
on public.documents for insert
with check (auth.uid() = user_id);

create policy "Users can delete own documents"
on public.documents for delete
using (auth.uid() = user_id);

create policy "Users can query chunks of own documents"
on public.chunks for select
using (
  exists (
    select 1 from public.documents
    where documents.id = chunks.document_id
    and documents.user_id = auth.uid()
  )
);

CREATE POLICY "Users can insert chunks for own documents"
ON public.chunks FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.documents
    WHERE documents.id = chunks.document_id
    AND documents.user_id = auth.uid()
  )
);


create policy "Users can see own conversations"
on public.conversations for all
using (auth.uid() = user_id);


create policy "Users can access messages of own conversations"
on public.messages for all
using (
  exists (
    select 1 from public.conversations
    where conversations.id = messages.conversation_id
    and conversations.user_id = auth.uid()
  )
);

CREATE POLICY "Users can see citations for their messages"
ON public.citations FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.messages
    JOIN public.conversations ON messages.conversation_id = conversations.id
    WHERE messages.id = citations.message_id
    AND conversations.user_id = auth.uid()
  )
);

CREATE POLICY "Users can insert citations for their messages"
ON public.citations 
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.messages
    JOIN public.conversations ON messages.conversation_id = conversations.id
    WHERE messages.id = citations.message_id
    AND conversations.user_id = auth.uid()
  )
);

CREATE POLICY "Users can delete citations for their messages"
ON public.citations 
FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM public.messages
    JOIN public.conversations ON messages.conversation_id = conversations.id
    WHERE messages.id = citations.message_id
    AND conversations.user_id = auth.uid()
  )
);




CREATE POLICY "Users can read their own documents"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'pdfs'
  AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can upload their own documents"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'pdfs' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete their own documents"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'pdfs' 
  AND auth.uid()::text = (storage.foldername(name))[1]
);




--  Semantic search
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1024),
  match_threshold float,
  match_count int,
  arg_document_id uuid,  
  arg_user_id uuid       
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
  RETURN QUERY
  SELECT
    chunks.id,
    chunks.content,
    chunks.metadata,
    1 - (chunks.embedding <=> query_embedding) AS similarity
  FROM chunks
  JOIN documents ON chunks.document_id = documents.id
  WHERE 1 - (chunks.embedding <=> query_embedding) > match_threshold
  AND chunks.document_id = arg_document_id  
  AND documents.user_id = arg_user_id       
  ORDER BY chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;