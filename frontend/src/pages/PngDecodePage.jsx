/**
 * pages/PngDecodePage.jsx
 * -----------------------
 * Mode: SoundPixel PNG → original audio file
 *
 * The user uploads a PNG created by PngEncodePage.
 * We unpack the pixel data back to bytes and verify the CRC-32 checksum.
 */

import React from 'react';
import { DropZone }      from '../components/DropZone';
import { ConvertButton } from '../components/ConvertButton';
import { ProgressBar }   from '../components/ProgressBar';
import { StatusMessage } from '../components/StatusMessage';
import { ResultCard }    from '../components/ResultCard';
import { useDropZone }   from '../hooks/useDropZone';
import { useConversion } from '../hooks/useConversion';
import { pngDecode }     from '../api';
import { formatBytes, isAudioFile, isImageFile } from '../utils/format';

export function PngDecodePage() {
  const dropZone   = useDropZone({ accept: 'image/png,.png' });
  const conversion = useConversion();

  const handleConvert = async () => {
    if (!dropZone.file) return;
    const file = dropZone.file;

    await conversion.run(async (setProgress) => {
      const res = await pngDecode(file, setProgress);

      // Decide which preview to show based on what was decoded
      const outputType = isAudioFile(res.filename) ? 'decoded-audio'
                       : isImageFile(res.filename) ? 'decoded-image'
                       : 'decoded-file';

      return {
        blob:           res.blob,
        filename:       res.filename,
        outputType,
        successMessage: `Decoded "${res.filename}" — CRC-32 verified, lossless ✓`,
        stats: {
          'Recovered file': res.filename,
          'Size':           formatBytes(res.outputSize),
          'PNG was':        formatBytes(file.size),
        },
      };
    });
  };

  const canConvert = !!dropZone.file && !conversion.busy;

  return (
    <div>
      <p className="text-xs text-muted2 leading-relaxed mb-6">
        Upload a SoundPixel PNG. The original file will be unpacked from the pixel
        data and verified with a CRC-32 checksum — guaranteeing a lossless recovery.
      </p>

      <DropZone
        label="Drop a SoundPixel PNG here"
        hint="Must be a PNG created by the MP3 → PNG encoder above"
        emoji="🖼️"
        {...dropZone}
        onClear={() => { dropZone.clearFile(); conversion.reset(); }}
      />

      {conversion.busy && <ProgressBar percent={conversion.progress} />}
      <StatusMessage status={conversion.status} />

      <ConvertButton
        label="Decode to Original File"
        disabled={!canConvert}
        busy={conversion.busy}
        onClick={handleConvert}
      />

      <ResultCard result={conversion.result} />
    </div>
  );
}