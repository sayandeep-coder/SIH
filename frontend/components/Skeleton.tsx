export function Skeleton({ width, height = 11, className = "" }: { width?: number | string; height?: number; className?: string }) {
  return <span className={`skel ${className}`} style={{ width, height, display: "block" }} />;
}

export function SkeletonText({ className = "" }: { className?: string }) {
  return <span className={`skel skel-text ${className}`} />;
}

export function SkeletonRows({ rows, cols }: { rows: number; cols: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr className="skel-row" key={r}>
          {Array.from({ length: cols }).map((_, c) => (
            <td key={c}><Skeleton /></td>
          ))}
        </tr>
      ))}
    </>
  );
}
