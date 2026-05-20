import { useCallback, useRef, useState } from 'react';
import { UploadCloud, FileSpreadsheet } from 'lucide-react';
import { cn } from '@/lib/utils';

const ACCEPT = '.csv,.xlsx,.xls,.pdf,.docx';

export function FileDropzone({
  onFile,
  disabled,
}: {
  onFile: (file: File) => void;
  disabled?: boolean;
}) {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDrag(false);
      if (disabled) return;
      const file = e.dataTransfer.files?.[0];
      if (file) onFile(file);
    },
    [onFile, disabled],
  );

  return (
    <label
      className={cn(
        'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition',
        drag ? 'border-primary-500 bg-primary-500/5' : 'border-border bg-surface-subtle/40 hover:bg-surface-subtle',
        disabled && 'cursor-not-allowed opacity-60',
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = '';
        }}
      />
      <UploadCloud className="mb-3 h-10 w-10 text-primary-500" />
      <div className="text-sm font-medium text-ink">Drop a CSV, Excel, PDF, or DOCX here</div>
      <div className="mt-1 flex items-center gap-1.5 text-xs text-ink-muted">
        <FileSpreadsheet className="h-3.5 w-3.5" /> or click to browse
      </div>
    </label>
  );
}
