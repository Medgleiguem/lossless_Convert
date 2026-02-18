/**
 * hooks/useConversion.js
 * ----------------------
 * Custom hook that encapsulates all conversion state:
 * progress, busy flag, status message, and the result object.
 *
 * Usage:
 *   const { busy, progress, status, result, run, reset } = useConversion();
 *   await run(() => pngEncode(file, setProgress));
 */

import { useState, useCallback, useRef } from 'react';

/**
 * @typedef {Object} ConversionStatus
 * @property {'success'|'error'} type
 * @property {string} message
 */

/**
 * @typedef {Object} ConversionResult
 * @property {string}   objectUrl  - blob URL for preview and download
 * @property {string}   filename   - suggested download filename
 * @property {Blob}     blob       - raw Blob
 * @property {string}   outputType - 'png' | 'audio' | 'image' | 'file'
 * @property {Object}   stats      - key/value pairs shown in the result card
 */

export function useConversion() {
  const [busy,     setBusy]     = useState(false);
  const [progress, setProgress] = useState(0);
  const [status,   setStatus]   = useState(/** @type {ConversionStatus|null} */ null);
  const [result,   setResult]   = useState(/** @type {ConversionResult|null} */ null);

  // Keep track of the previous object URL so we can revoke it on the next run
  const prevUrl = useRef(null);

  const reset = useCallback(() => {
    if (prevUrl.current) {
      URL.revokeObjectURL(prevUrl.current);
      prevUrl.current = null;
    }
    setBusy(false);
    setProgress(0);
    setStatus(null);
    setResult(null);
  }, []);

  /**
   * Run a conversion function.
   *
   * @param {() => Promise<ConversionResult>} conversionFn
   *   A function that calls one of the api.js methods and returns a ConversionResult.
   *   The function receives `setProgress` as its argument.
   */
  const run = useCallback(async (conversionFn) => {
    // Revoke previous object URL to avoid memory leaks
    if (prevUrl.current) {
      URL.revokeObjectURL(prevUrl.current);
      prevUrl.current = null;
    }

    setBusy(true);
    setProgress(5);
    setStatus(null);
    setResult(null);

    try {
      const convResult = await conversionFn(setProgress);

      const objectUrl = URL.createObjectURL(convResult.blob);
      prevUrl.current = objectUrl;

      setResult({ ...convResult, objectUrl });
      setStatus({ type: 'success', message: convResult.successMessage ?? 'Conversion complete — lossless ✓' });
    } catch (error) {
      setStatus({ type: 'error', message: error.message });
      setProgress(0);
    } finally {
      setBusy(false);
    }
  }, []);

  return { busy, progress, setProgress, status, result, run, reset };
}