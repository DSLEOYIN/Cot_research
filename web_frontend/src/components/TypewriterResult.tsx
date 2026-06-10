import { useEffect, useRef, useState } from 'react';
import { ResultRenderer } from './ResultRenderer';

type Props = {
  content: string;
  active: boolean;
};

export function TypewriterResult({ content, active }: Props) {
  const [visible, setVisible] = useState(active ? '' : content);
  const visibleRef = useRef(visible);
  const targetRef = useRef(content);
  const frameRef = useRef<number | null>(null);
  const lastFrameRef = useRef(0);
  const budgetRef = useRef(0);
  const pauseUntilRef = useRef(0);
  const isRevealing = active && visible.length < content.length;

  useEffect(() => {
    targetRef.current = content;
  }, [content]);

  useEffect(() => {
    if (!active) {
      targetRef.current = content;
      visibleRef.current = content;
      setVisible(content);
      return;
    }

    const punctuationPause = (character: string) => {
      if (/[。！？!?]/.test(character)) return 130;
      if (/[；;：:\n]/.test(character)) return 75;
      if (/[，,、]/.test(character)) return 35;
      return 0;
    };

    const tick = (now: number) => {
      const target = targetRef.current;
      if (!lastFrameRef.current) lastFrameRef.current = now;
      const elapsed = Math.min(now - lastFrameRef.current, 80);
      lastFrameRef.current = now;

      if (now >= pauseUntilRef.current && visibleRef.current.length < target.length) {
        budgetRef.current += elapsed * 0.065;
        const count = Math.min(Math.floor(budgetRef.current), 5);
        if (count > 0) {
          const next = target.slice(0, visibleRef.current.length + count);
          const lastCharacter = next[next.length - 1] || '';
          budgetRef.current -= count;
          visibleRef.current = next;
          setVisible(next);
          pauseUntilRef.current = now + punctuationPause(lastCharacter);
        }
      }
      frameRef.current = requestAnimationFrame(tick);
    };

    if (frameRef.current === null) {
      frameRef.current = requestAnimationFrame(tick);
    }
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      lastFrameRef.current = 0;
    };
  }, [active]);

  const lastLineBreak = visible.lastIndexOf('\n');
  const stableContent = lastLineBreak >= 0 ? visible.slice(0, lastLineBreak + 1) : '';
  const pendingText = lastLineBreak >= 0 ? visible.slice(lastLineBreak + 1) : visible;
  const pendingIsHeading = /^#{1,6}\s+/.test(pendingText);
  const pendingDisplayText = pendingText
    .replace(/^#{1,6}\s+/, '')
    .replace(/^\s*([-*_])(?:\s*\1){2,}\s*$/, '')
    .replace(/\*\*|__|`/g, '');

  return (
    <div className={`typewriter-result ${active ? 'active' : ''} ${isRevealing ? 'streaming-reveal' : ''}`}>
      {stableContent && <ResultRenderer content={stableContent} />}
      {pendingDisplayText && (
        <p className={`streaming-pending-text ${pendingIsHeading ? 'pending-heading' : ''}`}>{pendingDisplayText}</p>
      )}
    </div>
  );
}
