import fs from 'fs/promises';
import path from 'path';
import sharp from 'sharp';

const root = path.resolve(process.cwd());
const srcSvg = path.join(root, 'assets/images/riksahayak-logo.svg');
const outDir = path.join(root, 'assets/images');

const outputs = [
  { file: 'icon.png', size: 1024 },
  { file: 'favicon.png', size: 256 },
  { file: 'splash-icon.png', size: 512 },
  { file: 'android-icon-foreground.png', size: 432 },
  { file: 'android-icon-background.png', size: 432, type: 'solid', color: '#E6F4FE' },
  { file: 'android-icon-monochrome.png', size: 432, type: 'mono' },
];

async function ensureExists(filePath) {
  try {
    await fs.access(filePath);
  } catch {
    throw new Error(`Missing source: ${filePath}`);
  }
}

async function generate() {
  await ensureExists(srcSvg);
  await fs.mkdir(outDir, { recursive: true });

  for (const output of outputs) {
    const { file, size, type, color } = output;
    const out = path.join(outDir, file);

    if (type === 'solid') {
      // Generate solid color image
      await sharp({
        create: {
          width: size,
          height: size,
          channels: 4,
          background: color,
        },
      })
        .png()
        .toFile(out);
      console.log(`Generated ${file} (${size}x${size} solid ${color})`);
    } else if (type === 'mono') {
      // Generate monochrome version (black fill)
      const svgBuffer = await fs.readFile(srcSvg);
      const monoSvg = svgBuffer.toString().replace(/fill="#FCFDFC"/g, 'fill="#000000"');
      await sharp(Buffer.from(monoSvg))
        .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .png()
        .toFile(out);
      console.log(`Generated ${file} (${size}x${size} monochrome)`);
    } else {
      // Default: resize SVG
      await sharp(srcSvg)
        .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .png()
        .toFile(out);
      console.log(`Generated ${file} (${size}x${size})`);
    }
  }
}

generate().catch((err) => {
  console.error('Icon generation failed:', err);
  process.exit(1);
});
