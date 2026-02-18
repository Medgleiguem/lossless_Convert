/**
 * pages/PngEncodePage.jsx
 * -----------------------
 * Mode: MP3 (or any audio) → SoundPixel PNG
 *
 * The user uploads an audio file. We encode every byte into RGB pixels
 * of a PNG image. The PNG can later be decoded back to the original audio.
 */

import React from 'react';
import { DropZone }      from '../components/DropZone';
import { ConvertButton } from '../components/ConvertButton';
import { ProgressBar }   from '../components/ProgressBar';
import { StatusMessage } from '../components/StatusMessage';
import { ResultCard }    from '../components/ResultCard';
import { useDropZone }   from '../hooks/useDropZone';
import { useConversion } from '../hooks/useConversion';
import { pngEncode }     from '../api';
import { formatBytes }   from '../utils/format';

export function PngEncodePage() {
  const dropZone   = useDropZone({ accept: 'audio/*,.mp3,.wav,.flac,.ogg,.aac,.m4a,.opus,.aiff' });
  const conversion = useConversion();

  const handleConvert = async () => {
    if (!dropZone.file) return;
    const file = dropZone.file;

    await conversion.run(async (setProgress) => {
      const res = await pngEncode(file, setProgress);
      return {
        blob:           res.blob,
        filename:       res.filename,
        outputType:     'encoded-png',
        successMessage: `Encoded into a ${res.width}×${res.height} PNG — lossless ✓`,
        stats: {
          'Input':      formatBytes(res.inputSize),
          'PNG size':   formatBytes(res.outputSize),
          'Dimensions': `${res.width} × ${res.height} px`,
        },
      };
    });
  };

  const canConvert = !!dropZone.file && !conversion.busy;

  return (
    <div>
      <p className="text-xs text-muted2 leading-relaxed mb-6">
        Upload any audio file. Every byte will be packed into the RGB channels of
        a lossless PNG image. The PNG can be decoded back to the exact original file.
      </p>

      <DropZone
        label="Drop your audio file here"
        hint="MP3, WAV, FLAC, OGG, AAC, AIFF — any format"
        emoji="🎵"
        {...dropZone}
        onClear={() => { dropZone.clearFile(); conversion.reset(); }}
      />

      {conversion.busy && <ProgressBar percent={conversion.progress} />}
      <StatusMessage status={conversion.status} />

      <ConvertButton
        label="Encode to PNG"
        disabled={!canConvert}
        busy={conversion.busy}
        onClick={handleConvert}
      />

      <ResultCard result={conversion.result} />
    </div>
  );
}