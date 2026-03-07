import { useState, useCallback } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { FiCopy, FiCheck } from 'react-icons/fi'

function CodeBlock({ language, children }) {
    const [copied, setCopied] = useState(false)

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(children)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }, [children])

    return (
        <div className="code-block-wrapper">
            <div className="code-block-header">
                <span>{language}</span>
                <button className="copy-btn" onClick={handleCopy}>
                    {copied ? (
                        <>
                            <FiCheck size={12} /> Copied
                        </>
                    ) : (
                        <>
                            <FiCopy size={12} /> Copy
                        </>
                    )}
                </button>
            </div>
            <SyntaxHighlighter
                language={language}
                style={oneLight}
                customStyle={{
                    margin: 0,
                    padding: '16px',
                    fontSize: '0.85em',
                    background: '#FAFAFA',
                    border: 'none',
                    borderRadius: 0,
                }}
                wrapLongLines
            >
                {children}
            </SyntaxHighlighter>
        </div>
    )
}

export default function MarkdownRenderer({ content }) {
    return (
        <div className="markdown-body">
            <Markdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex, rehypeRaw]}
                components={{
                    pre({ children }) {
                        return <>{children}</>
                    },
                    code({ className, children, ...props }) {
                        const codeString = String(children).replace(/\n$/, '')
                        const langMatch = /language-(\w+)/.exec(className || '')

                        const isBlock = !!langMatch || codeString.includes('\n')

                        if (isBlock) {
                            return (
                                <CodeBlock language={langMatch?.[1] || 'text'}>
                                    {codeString}
                                </CodeBlock>
                            )
                        }
                        return <code className={className} {...props}>{children}</code>
                    },
                }}
            >
                {content}
            </Markdown>
        </div>
    )
}
