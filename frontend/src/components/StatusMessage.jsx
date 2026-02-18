/**
 * components/StatusMessage.jsx
 * ----------------------------
 * Displays a success or error message after a conversion.
 */

import React from 'react';

export function StatusMessage({ status }) {
  if (!status) return null;

  const isSuccess = status.type === 'success';

  return (
    <div className={[
      'flex items-start gap-2 px-4 py-3 mt-3 rounded-md border text-xs leading-relaxed',
      isSuccess
        ? 'bg-success/[0.06] border-success/30 text-success'
        : 'bg-error/[0.06]   border-error/30   text-error',
    ].join(' ')}>
      <span className="flex-shrink-0 font-bold">{isSuccess ? '✓' : '✕'}</span>
      <span>{status.message}</span>
    </div>
  );
}