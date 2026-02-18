/**
 * pages/Mp3DecodePage.jsx
 * -----------------------
 * Mode: Extract the hidden image from a SoundPixel MP3
 *
 * The user uploads a SoundPixel MP3 (created by Mp3EncodePage).
 * We find the hidden block after the audio frames, verify CRC-32,
 * and return the original image.
 */

import React from 'react';
import { DropZone }      from '../components/DropZone';
import { ConvertButton } from '../components/ConvertButton';
import { ProgressBar }   from '../components/ProgressBar';
import { StatusMessage } from '../components/StatusMessage';
import { ResultCard }    from '../components/ResultCard';
import { useDropZone }   from '../hooks/useDropZone';
import { useConversion } from '../hooks/useConversion';
import { mp3Decode }     from '../api';
import { formatBytes }   from '../utils/format';

export function Mp3DecodePage() {
  const dropZone   = useDropZone({ accept: 'audio/mpeg,.mp3' });
  const conversion = useConversion();

  const handleConvert = async () => {
    if (!dropZone.file) return;
    const file = dropZone.file;

    await conversion.run(async (setProgress) => {
      const res = await mp3Decode(file, setProgress);
      return {
        blob:           res.blob,
        filename:       res.filename,
        outputType:     'decoded-image',
        successMessage: `Extracted "${res.filename}" — CRC-32 verified, lossless ✓`,
        stats: {
          'Image':    res.filename,
          'Size':     formatBytes(res.outputSize),
          'MP3 was':  formatBytes(file.size),
        },
      };
    });
  };

  const canConvert = !!dropZone.file && !conversion.busy;

  return (
    <div>
      <p className="text-xs text-muted2 leading-relaxed mb-6">
        Upload a SoundPixel MP3 that was created by the steganography encoder.
        The hidden image will be extracted and verified — guaranteed identical
        to what was embedded.
      </p>

      <DropZone
        label="Drop a SoundPixel MP3 here"
        hint="Must be an MP3 created by the 'Hide Image in MP3' encoder"
        emoji="🔍"
        {...dropZone}
        onClear={() => { dropZone.clearFile(); conversion.reset(); }}
      />

      {conversion.busy && <ProgressBar percent={conversion.progress} />}
      <StatusMessage status={conversion.status} />

      <ConvertButton
        label="Extract Hidden Image"
        disabled={!canConvert}
        busy={conversion.busy}
        onClick={handleConvert}
      />

      <ResultCard result={conversion.result} />
    </div>
  );
}