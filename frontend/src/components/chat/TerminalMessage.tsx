import { useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { type Message } from '@/store/tarsStore';
import { useTarsRobotStore } from '@/store/tarsRobotStore';
import { CodeBlock } from '@/components/ui/CodeBlock';

interface TerminalMessageProps {
  message: Message;
}

// Parse content for gestures and clean it up
function parseGestures(content: string): { cleanContent: string; gestures: string[] } {
  // Extract gestural text like *Sigh*, *cue light dims*, etc.
  // We use a stricter regex that avoids matching across newlines or long blocks
  // to prevent false positives in code markers or italics
  const gesturePattern = /\*([^*]{3,50})\*/g;
  const gestures: string[] = [];
  let match;

  while ((match = gesturePattern.exec(content)) !== null) {
    gestures.push(match[1]);
  }

  // Remove gestural text from content
  const cleanContent = content.replace(gesturePattern, '').trim();

  return { cleanContent, gestures };
}

export function TerminalMessage({ message }: TerminalMessageProps) {
  const isUser = message.role === 'user';
  const setGesture = useTarsRobotStore((state) => state.setGesture);

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  // Process Gestures FIRST (only for TARS messages)
  const { cleanContent, gestures } = useMemo(() => {
    if (isUser) return { cleanContent: message.content || '', gestures: [] };
    return parseGestures(message.content || '');
  }, [isUser, message.content]);

  // Route gestures to the robot
  useEffect(() => {
    if (!isUser && gestures.length > 0) {
      gestures.forEach((gesture) => setGesture(gesture));
    }
  }, [message.id, isUser, gestures, setGesture]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "group font-terminal text-sm leading-relaxed",
        isUser ? "text-tars-light" : "text-tars-light/90"
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-1">
        {/* Timestamp */}
        <span className="text-[10px] text-muted-foreground tabular-nums">
          [{formatTime(message.timestamp)}]
        </span>

        {/* Source indicator */}
        <span className={cn(
          "text-[10px] uppercase tracking-wider",
          isUser ? "text-tars-blue" : "text-tars-amber"
        )}>
          {isUser ? 'OPERATOR' : 'TARS'}
        </span>

        {/* Streaming indicator */}
        {message.isStreaming && (
          <motion.span
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="text-[10px] text-tars-amber"
          >
            ▌
          </motion.span>
        )}
      </div>

      {/* Content */}
      <div className={cn(
        "pl-4 border-l",
        isUser ? "border-tars-blue/30" : "border-tars-amber/30"
      )}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-p:my-2 prose-pre:my-0 prose-pre:bg-transparent prose-pre:p-0">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Untrusted model/source text must not trigger automatic network
                // requests through Markdown images (including tracking URLs).
                img: () => null,
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !match && !String(children).includes('\n');

                  if (match) {
                    return (
                      <CodeBlock
                        code={String(children).replace(/\n$/, '')}
                        language={match[1]}
                      />
                    );
                  }

                  return (
                    <code className={cn("bg-tars-dark/50 px-1 py-0.5 rounded text-tars-amber font-medium", className)} {...props}>
                      {children}
                    </code>
                  );
                },
                // Custom styles for markdown elements to match TARS aesthetic
                p: ({ children }) => <p className="leading-relaxed mb-2 text-tars-light/90">{children}</p>,
                strong: ({ children }) => <strong className="font-bold text-tars-light">{children}</strong>,
                em: ({ children }) => <em className="italic text-tars-light/80">{children}</em>,
                ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 my-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 space-y-1 my-2">{children}</ol>,
                li: ({ children }) => <li className="pl-1">{children}</li>,
                h1: ({ children }) => <h1 className="text-lg font-bold text-tars-blue mt-4 mb-2 uppercase tracking-wider">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold text-tars-amber mt-3 mb-2 uppercase">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold text-tars-green mt-2 mb-1">{children}</h3>,
                a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-tars-blue hover:underline underline-offset-2 transition-colors">{children}</a>,
                blockquote: ({ children }) => <blockquote className="border-l-2 border-tars-amber/40 pl-4 italic text-muted-foreground my-2">{children}</blockquote>,
              }}
            >
              {cleanContent}
            </ReactMarkdown>

            {/* Blinking cursor at the absolute end if streaming */}
            {message.isStreaming && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="inline-block w-2 h-4 bg-tars-amber ml-0.5 align-middle"
              />
            )}
          </div>
        )}

        {/* Metadata (for TARS responses) */}
        {!isUser && message.confidence !== undefined && (
          <div className="flex items-center gap-4 mt-2 pt-2 border-t border-border/30">
            <span className="text-[10px] text-muted-foreground">
              CONFIDENCE: <span className="text-tars-green">{message.confidence}%</span>
            </span>
            {message.source && (
              <span className="text-[10px] text-muted-foreground">
                SOURCE: <span className="text-tars-amber">{message.source}</span>
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
