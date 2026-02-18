/**
 * hooks/useDropZone.js
 * --------------------
 * Reusable drag-and-drop + file-input logic.
 * Returns props to spread onto a drop zone div and a hidden file input.
 *
 * Usage:
 *   const { file, dropZoneProps, inputProps, inputRef, clearFile } = useDropZone();
 */

import { useState, useRef, useCallback } from 'react';

/**
 * @param {Object}  options
 * @param {string}  options.accept   - file input accept attribute
 * @param {function} options.onChange - called with the selected File
 */
export function useDropZone({ accept = '*/*', onChange } = {}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [file, setFile]             = useState(null);
  const inputRef                    = useRef(null);

  const selectFile = useCallback((f) => {
    if (!f) return;
    setFile(f);
    onChange?.(f);
  }, [onChange]);

  const clearFile = useCallback(() => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = '';
    onChange?.(null);
  }, [onChange]);

  // Props to spread onto the drop zone <div>
  const dropZoneProps = {
    onDragOver:  (e) => { e.preventDefault(); setIsDragOver(true); },
    onDragLeave: ()  => setIsDragOver(false),
    onDrop:      (e) => {
      e.preventDefault();
      setIsDragOver(false);
      selectFile(e.dataTransfer.files[0]);
    },
    onClick: () => inputRef.current?.click(),
  };

  // Props to spread onto the hidden <input type="file">
  const inputProps = {
    type:     'file',
    accept,
    ref:      inputRef,
    style:    { display: 'none' },
    onChange: (e) => selectFile(e.target.files[0]),
  };

  return { file, isDragOver, dropZoneProps, inputProps, inputRef, clearFile };
}