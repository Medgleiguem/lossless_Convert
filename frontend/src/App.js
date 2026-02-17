import React, { useState, useRef, useCallback, useEffect } from 'react';
import styled, { keyframes, createGlobalStyle } from 'styled-components';
import { encodeAudio, decodeImage } from './api';


const fadeUp = keyframes`
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
`;

const scanline = keyframes`
  0%   { transform: translateY(-100%); }
  100% { transform: translateY(100vh); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
`;

const spin = keyframes`
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
`;

const progressGlow = keyframes`
  0%   { box-shadow: 0 0 6px var(--accent); }
  50%  { box-shadow: 0 0 20px var(--accent), 0 0 40px var(--accent); }
  100% { box-shadow: 0 0 6px var(--accent); }
`;

const GridBg = createGlobalStyle`
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(0, 229, 255, 0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 229, 255, 0.025) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
  }
  body::after {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.4;
    animation: ${scanline} 6s linear infinite;
    pointer-events: none;
    z-index: 999;
  }
`;


const Wrap = styled.div`
  position: relative;
  z-index: 1;
  max-width: 860px;
  margin: 0 auto;
  padding: 48px 24px 100px;
`;


const HeaderTag = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--accent);
  border: 1px solid rgba(0,229,255,0.3);
  padding: 5px 14px;
  margin-bottom: 24px;
  animation: ${fadeUp} 0.5s both;
  
  &::before {
    content: '';
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: ${pulse} 2s infinite;
  }
`;

const H1 = styled.h1`
  font-family: var(--font-disp);
  font-size: clamp(32px, 6vw, 64px);
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -0.04em;
  margin-bottom: 16px;
  animation: ${fadeUp} 0.5s 0.1s both;
  
  span { color: var(--accent); }
  em {
    font-style: normal;
    color: var(--accent2);
  }
`;

const Subtitle = styled.p`
  font-size: 12px;
  color: var(--muted2);
  letter-spacing: 0.06em;
  line-height: 1.7;
  max-width: 480px;
  animation: ${fadeUp} 0.5s 0.2s both;
`;


const ModeRow = styled.div`
  display: flex;
  gap: 0;
  margin: 40px 0 32px;
  animation: ${fadeUp} 0.5s 0.25s both;
`;

const ModeBtn = styled.button`
  flex: 1;
  max-width: 220px;
  padding: 13px 24px;
  border: 1px solid var(--border2);
  background: ${p => p.$active ? 'var(--accent)' : 'var(--surface)'};
  color: ${p => p.$active ? '#000' : 'var(--muted2)'};
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  transition: all 0.2s;
  
  &:first-child { border-radius: 4px 0 0 4px; }
  &:last-child  { border-radius: 0 4px 4px 0; }
  
  &:not([disabled]):hover {
    border-color: var(--accent);
    color: ${p => p.$active ? '#000' : 'var(--accent)'};
  }
`;


const DropOuter = styled.div`
  animation: ${fadeUp} 0.5s 0.3s both;
`;

const DropZone = styled.div`
  position: relative;
  border: 1px dashed ${p => p.$dragover ? 'var(--accent)' : 'var(--border2)'};
  border-radius: 8px;
  padding: 56px 32px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  background: ${p => p.$dragover ? 'rgba(0,229,255,0.04)' : 'var(--surface)'};
  
  &:hover {
    border-color: var(--accent);
    background: rgba(0,229,255,0.02);
  }
  
  /* Corner marks */
  &::before, &::after {
    content: '';
    position: absolute;
    width: 16px; height: 16px;
    border-color: var(--accent);
    border-style: solid;
    opacity: 0.5;
  }
  &::before { top: 8px; left: 8px; border-width: 2px 0 0 2px; }
  &::after  { bottom: 8px; right: 8px; border-width: 0 2px 2px 0; }
`;

const UploadIcon = styled.div`
  width: 56px; height: 56px;
  margin: 0 auto 20px;
  border: 1px solid var(--border2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: var(--surface2);
  transition: all 0.2s;
  
  ${DropZone}:hover & {
    border-color: var(--accent);
    background: rgba(0,229,255,0.08);
  }
`;

const DropLabel = styled.div`
  font-family: var(--font-disp);
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.01em;
`;

const DropSub = styled.div`
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.05em;
  
  span {
    color: var(--accent);
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 3px;
  }
`;


const FileChip = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 6px;
  margin-top: 12px;
`;

const FileIcon = styled.div`
  width: 36px; height: 36px;
  background: rgba(0,229,255,0.1);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
`;

const FileDetails = styled.div`
  flex: 1;
  min-width: 0;
`;

const FileName = styled.div`
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const FileSize = styled.div`
  font-size: 10px;
  color: var(--muted);
  margin-top: 2px;
  letter-spacing: 0.05em;
`;

const RemoveBtn = styled.button`
  background: none;
  border: none;
  color: var(--muted);
  font-size: 16px;
  padding: 4px;
  line-height: 1;
  transition: color 0.2s;
  &:hover { color: var(--error); }
`;


const ConvertBtn = styled.button`
  display: block;
  width: 100%;
  margin-top: 20px;
  padding: 16px;
  background: ${p => p.disabled ? 'var(--surface2)' : 'var(--accent)'};
  color: ${p => p.disabled ? 'var(--muted)' : '#000'};
  border: 1px solid ${p => p.disabled ? 'var(--border2)' : 'var(--accent)'};
  border-radius: 6px;
  font-family: var(--font-disp);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  transition: all 0.2s;
  cursor: ${p => p.disabled ? 'not-allowed' : 'pointer'};
  animation: ${fadeUp} 0.5s 0.35s both;
  
  &:not(:disabled):hover {
    background: #33ebff;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0,229,255,0.25);
  }
  &:not(:disabled):active { transform: none; }
`;


const ProgressWrap = styled.div`
  margin-top: 14px;
  height: 2px;
  background: var(--border);
  border-radius: 1px;
  overflow: hidden;
`;

const ProgressFill = styled.div`
  height: 100%;
  width: ${p => p.$pct}%;
  background: var(--accent);
  border-radius: 1px;
  transition: width 0.3s;
  animation: ${progressGlow} 1.5s infinite;
`;


const Status = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 14px;
  border: 1px solid;
  
  ${p => p.$type === 'success' && `
    background: rgba(0, 229, 160, 0.07);
    border-color: rgba(0, 229, 160, 0.3);
    color: var(--success);
  `}
  ${p => p.$type === 'error' && `
    background: rgba(255, 61, 113, 0.07);
    border-color: rgba(255, 61, 113, 0.3);
    color: var(--error);
  `}
`;


const ResultSection = styled.div`
  margin-top: 36px;
  animation: ${fadeUp} 0.4s both;
`;

const SectionLabel = styled.div`
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }
`;

const ResultCard = styled.div`
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 8px;
  overflow: hidden;
`;

const ResultPreview = styled.div`
  padding: 32px;
  background: repeating-conic-gradient(
    var(--surface2) 0% 25%,
    var(--bg) 0% 50%
  ) 0 0 / 20px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
`;

const PreviewImg = styled.img`
  max-width: 100%;
  max-height: 280px;
  image-rendering: pixelated;
  border-radius: 3px;
  border: 1px solid var(--border2);
`;

const AudioBlock = styled.div`
  text-align: center;
`;

const AudioTitle = styled.div`
  font-family: var(--font-disp);
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 14px;
  letter-spacing: -0.01em;
`;

const AudioPlayer = styled.audio`
  width: 100%;
  max-width: 340px;
  filter: invert(1) hue-rotate(190deg) saturate(0.6);
`;

const ResultMeta = styled.div`
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
`;

const StatRow = styled.div`
  display: flex;
  gap: 24px;
`;

const Stat = styled.div``;

const StatLabel = styled.div`
  font-size: 9px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
`;

const StatValue = styled.div`
  font-size: 12px;
  font-weight: 700;
  margin-top: 2px;
  color: var(--text);
`;

const DownloadBtn = styled.a`
  padding: 10px 20px;
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  border-radius: 5px;
  font-family: var(--font-mono);
  font-size: 11px;
  text-decoration: none;
  letter-spacing: 0.08em;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  text-transform: uppercase;
  
  &:hover {
    background: var(--accent);
    color: #000;
  }
`;


const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1px;
  margin-top: 60px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  animation: ${fadeUp} 0.5s 0.5s both;
`;

const InfoCard = styled.div`
  padding: 20px;
  background: var(--surface);
  transition: background 0.2s;
  
  &:hover { background: var(--surface2); }
`;

const InfoIcon = styled.div`
  font-size: 20px;
  margin-bottom: 10px;
`;

const InfoTitle = styled.div`
  font-family: var(--font-disp);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
  color: var(--accent);
`;

const InfoText = styled.div`
  font-size: 11px;
  color: var(--muted2);
  line-height: 1.6;
`;

const Footer = styled.footer`
  text-align: center;
  padding-top: 48px;
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  animation: ${fadeUp} 0.5s 0.6s both;
`;


function formatBytes(n) {
  if (!n) return '—';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

function fileEmoji(name = '') {
  const ext = name.split('.').pop().toLowerCase();
  const map = { mp3: '🎵', wav: '🔊', flac: '🎼', ogg: '🎶', aac: '🎧', m4a: '🎵', png: '🖼️' };
  return map[ext] || '📁';
}


export default function App() {
  const [mode, setMode] = useState('encode'); // 'encode' | 'decode'
  const [file, setFile] = useState(null);
  const [dragover, setDragover] = useState(false);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success'|'error', msg }
  const [result, setResult] = useState(null);

  const fileRef = useRef(null);

  useEffect(() => {
    return () => {
      if (result?.objectUrl) URL.revokeObjectURL(result.objectUrl);
    };
  }, [result]);

  const reset = useCallback(() => {
    setFile(null);
    setStatus(null);
    setResult(null);
    setProgress(0);
    if (fileRef.current) fileRef.current.value = '';
  }, []);

  const switchMode = useCallback((m) => {
    setMode(m);
    reset();
  }, [reset]);

  const handleFile = useCallback((f) => {
    if (!f) return;
    if (result?.objectUrl) URL.revokeObjectURL(result.objectUrl);
    setFile(f);
    setStatus(null);
    setResult(null);
    setProgress(0);
  }, [result]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragover(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const convert = useCallback(async () => {
    if (!file || busy) return;
    setBusy(true);
    setStatus(null);
    setResult(null);
    setProgress(5);

    try {
      let res;
      if (mode === 'encode') {
        res = await encodeAudio(file, setProgress);
        const objectUrl = URL.createObjectURL(res.blob);
        setResult({
          objectUrl,
          filename: res.filename,
          blob: res.blob,
          type: 'image',
          metadata: {
            'Dimensions': `${res.width} × ${res.height} px`,
            'PNG size': formatBytes(res.blob.size),
            'Original': formatBytes(res.originalSize),
          },
        });
      } else {
        res = await decodeImage(file, setProgress);
        const objectUrl = URL.createObjectURL(res.blob);
        setResult({
          objectUrl,
          filename: res.filename,
          blob: res.blob,
          type: 'audio',
          metadata: {
            'File': res.filename,
            'Size': formatBytes(res.decodedSize),
            'PNG was': formatBytes(file.size),
          },
        });
      }
      setStatus({ type: 'success', msg: 'Conversion complete — lossless integrity verified ✓' });
    } catch (err) {
      setStatus({ type: 'error', msg: err.message });
      setProgress(0);
    } finally {
      setBusy(false);
    }
  }, [file, busy, mode]);

  const accept = mode === 'encode' ? '*/*' : 'image/png';
  const dropLabel = mode === 'encode' ? 'Drop your audio file here' : 'Drop a SoundPixel PNG here';

  return (
    <>
      <GridBg />
      <Wrap>
        <header>
          <HeaderTag>Lossless Audio Codec v1.0</HeaderTag>
          <H1>Sound<span>Pixel</span></H1>
          <Subtitle>
            Convert any audio file into a lossless PNG image — and perfectly reconstruct the original.
            Every byte preserved. CRC-32 verified.
          </Subtitle>
        </header>

        <ModeRow>
          <ModeBtn $active={mode === 'encode'} onClick={() => switchMode('encode')}>
            ▶ Audio → Image
          </ModeBtn>
          <ModeBtn $active={mode === 'decode'} onClick={() => switchMode('decode')}>
            ◀ Image → Audio
          </ModeBtn>
        </ModeRow>

        <DropOuter>
          <DropZone
            $dragover={dragover}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
            onDragLeave={() => setDragover(false)}
            onDrop={handleDrop}
          >
            <UploadIcon>{mode === 'encode' ? '🎵' : '🖼️'}</UploadIcon>
            <DropLabel>{dropLabel}</DropLabel>
            <DropSub>
              drag &amp; drop or{' '}
              <span onClick={(e) => { e.stopPropagation(); fileRef.current?.click(); }}>
                browse files
              </span>
              {mode === 'encode' ? ' · MP3, WAV, FLAC, OGG, AAC, any format' : ' · only SoundPixel PNGs'}
            </DropSub>
          </DropZone>

          <input
            ref={fileRef}
            type="file"
            accept={accept}
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />

          {file && (
            <FileChip>
              <FileIcon>{fileEmoji(file.name)}</FileIcon>
              <FileDetails>
                <FileName>{file.name}</FileName>
                <FileSize>{formatBytes(file.size)}</FileSize>
              </FileDetails>
              <RemoveBtn onClick={reset}>✕</RemoveBtn>
            </FileChip>
          )}
        </DropOuter>

        {busy && (
          <ProgressWrap>
            <ProgressFill $pct={progress} />
          </ProgressWrap>
        )}

        {status && (
          <Status $type={status.type}>
            {status.type === 'success' ? '✓' : '✕'}&nbsp;{status.msg}
          </Status>
        )}

        <ConvertBtn disabled={!file || busy} onClick={convert}>
          {busy ? '⟳ Converting…' : mode === 'encode' ? 'Encode to PNG' : 'Decode to Audio'}
        </ConvertBtn>

        {result && (
          <ResultSection>
            <SectionLabel>Result</SectionLabel>
            <ResultCard>
              <ResultPreview>
                {result.type === 'image' ? (
                  <PreviewImg src={result.objectUrl} alt="Encoded PNG" />
                ) : (
                  <AudioBlock>
                    <AudioTitle>🎵 {result.filename}</AudioTitle>
                    <AudioPlayer controls src={result.objectUrl} />
                  </AudioBlock>
                )}
              </ResultPreview>
              <ResultMeta>
                <StatRow>
                  {Object.entries(result.metadata).map(([k, v]) => (
                    <Stat key={k}>
                      <StatLabel>{k}</StatLabel>
                      <StatValue>{v}</StatValue>
                    </Stat>
                  ))}
                </StatRow>
                <DownloadBtn href={result.objectUrl} download={result.filename}>
                  ↓ Download
                </DownloadBtn>
              </ResultMeta>
            </ResultCard>
          </ResultSection>
        )}

        <InfoGrid>
          {[
            { icon: '🔒', title: '100% Lossless', text: 'CRC-32 checksum verifies every decode. The output is bit-for-bit identical to the original.' },
            { icon: '🖼️', title: 'PNG Storage', text: 'Raw bytes packed 3-per-pixel into RGB channels. Always saved as PNG, never JPEG.' },
            { icon: '🎛️', title: 'Any Audio Format', text: 'Works with MP3, WAV, FLAC, OGG, AAC, AIFF — anything. It encodes raw bytes, not audio.' },
            { icon: '📦', title: 'Self-contained', text: 'The original filename is embedded in the image header. No sidecar files needed.' },
          ].map(({ icon, title, text }) => (
            <InfoCard key={title}>
              <InfoIcon>{icon}</InfoIcon>
              <InfoTitle>{title}</InfoTitle>
              <InfoText>{text}</InfoText>
            </InfoCard>
          ))}
        </InfoGrid>

        <Footer>SoundPixel · Lossless Audio ↔ PNG Codec · Python + React</Footer>
      </Wrap>
    </>
  );
}
