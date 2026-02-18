/**
 * pages/Mp3EncodePage.jsx
 * -----------------------
 * Mode: Hide an image inside an MP3 (steganography)
 *
 * The user uploads an MP3 (the carrier) and an image to hide.
 * The image bytes are appended after the last MP3 audio frame.
 * The resulting file plays normally in any audio player.
 */

import React from 'react';
import { DropZone }      from '../components/DropZone';
import { ConvertButton } from '../components/ConvertButton';
import { ProgressBar }   from '../components/ProgressBar';
import { StatusMessage } from '../components/StatusMessage';
import { ResultCard }    from '../components/ResultCard';
import { useDropZone }   from '../hooks/useDropZone';
import { useConversion } from '../hooks/useConversion';
import { mp3Encode }     from '../api';
import { formatBytes }   from '../utils/format';

export function Mp3EncodePage() {
  const mp3Drop    = useDropZone({ accept: 'audio/mpeg,.mp3' });
  const imageDropd = useDropZone({ accept: 'image/*,.png,.jpg,.jpeg,.gif,.webp,.bmp,.tiff' });
  const conversion = useConversion();

  const handleConvert = async () => {
    if (!mp3Drop.file || !imageDropd.file) return;

    const mp3File   = mp3Drop.file;
    const imageFile = imageDropd.file;

    await conversion.run(async (setProgress) => {
      const res = await mp3Encode(mp3File, imageFile, setProgress);
      return {
        blob:           res.blob,
        filename:       res.filename,
        outputType:     'encoded-mp3',
        successMessage: 'Image embedded — the MP3 still plays as normal audio ✓',
        stats: {
          'Audio':    formatBytes(res.mp3Size),
          'Image':    formatBytes(res.imageSize),
          'Total':    formatBytes(res.totalSize),
        },
      };
    });
  };

  const clearAll = () => {
    mp3Drop.clearFile();
    imageDropd.clearFile();
    conversion.reset();
  };

  const canConvert = !!mp3Drop.file && !!imageDropd.file && !conversion.busy;

  return (
    <div>
      <p className="text-xs text-muted2 leading-relaxed mb-6">
        Provide an MP3 file as the carrier and an image to hide inside it.
        The resulting MP3 plays as normal audio in any player, but contains
        your image — extractable with the decoder below.
      </p>

      {/* Two drop zones side by side */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <DropZone
          label="Carrier MP3"
          hint="The audio that will carry your image"
          emoji="🎵"
          {...mp3Drop}
          onClear={() => { mp3Drop.clearFile(); conversion.reset(); }}
        />

        <DropZone
          label="Image to hide"
          hint="PNG, JPG, GIF, WEBP — any image format"
          emoji="🖼️"
          {...imageDropd}
          onClear={() => { imageDropd.clearFile(); conversion.reset(); }}
        />
      </div>

      {/* Arrow between columns (visual hint) */}
      {mp3Drop.file && imageDropd.file && (
        <p className="text-center text-xs text-muted mt-3">
          🎵 <span className="text-accent mx-2">+</span> 🖼️
          <span className="text-muted mx-2">→</span>
          <span className="text-accent2">SoundPixel MP3</span>
        </p>
      )}

      {conversion.busy && <ProgressBar percent={conversion.progress} />}
      <StatusMessage status={conversion.status} />

      <ConvertButton
        label="Embed Image into MP3"
        disabled={!canConvert}
        busy={conversion.busy}
        onClick={handleConvert}
      />

      <ResultCard result={conversion.result} />
    </div>
  );
}