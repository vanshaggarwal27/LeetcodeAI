# LeetLog AI - Brand Guidelines

This document defines the official branding and visual identity for LeetLog AI.

## Logo Files

### Primary Logo
- **`logo.svg`** - Vector format (recommended for all uses)
- Scalable to any size without quality loss
- Use for: GitHub README, website, social media, presentations

### Additional Formats (To Generate)

From the `logo.svg` file, you can generate:

**PNG Exports** (using Inkscape, Adobe Illustrator, or online converter):
- `logo-128.png` - 128x128px (GitHub profile, small icons)
- `logo-256.png` - 256x256px (Social media, medium uses)
- `logo-512.png` - 512x512px (High-resolution displays, hero images)

**Favicon**:
- `favicon.ico` - 16x16, 32x32, 48x48 multi-size ICO file
- Convert from PNG using https://favicon.io or similar tool

## Color Palette

### Primary Colors

**Deep Navy Blue** - Background / Primary
- Hex: `#1e3a8a`
- RGB: `rgb(30, 58, 138)`
- Use: Logo background, headers, primary branding elements

**Sky Blue** - Accent / Interactive
- Hex: `#60a5fa`
- RGB: `rgb(96, 165, 250)`
- Use: Neural network nodes, connections, accents, links

**Medium Blue** - Support
- Hex: `#3b82f6`
- RGB: `rgb(59, 130, 246)`
- Use: Brain icon fill, secondary elements

**Amber Gold** - Highlight / Code
- Hex: `#fbbf24`
- RGB: `rgb(251, 191, 36)`
- Use: Code brackets, "AI" text, call-to-action elements

### Usage Guidelines

- **Background**: Use `#1e3a8a` (Deep Navy Blue) for dark themes
- **Text on Dark**: Use `#60a5fa` (Sky Blue) or `#fbbf24` (Amber Gold)
- **Interactive Elements**: Use `#60a5fa` for hover states and clickable items
- **Code/Tech Elements**: Use `#fbbf24` to highlight coding-related content

## Logo Design Elements

### Components

1. **Neural Network Pattern**: Represents AI/machine learning capabilities
   - Curved paths connecting nodes
   - Sky blue color (`#60a5fa`) with 60% opacity

2. **Neurons/Nodes**: 7 circular nodes forming a neural network
   - Small circles (4px radius)
   - Sky blue color (`#60a5fa`)

3. **Code Brackets**: `< >` symbols representing coding/programming
   - Monospace font, 48px size
   - Amber gold color (`#fbbf24`)
   - Positioned to frame the brain

4. **Central Brain Icon**: Stylized brain representing intelligence
   - Medium blue fill (`#3b82f6`)
   - Simplified with 3 fold lines
   - Centered in logo

5. **"AI" Text**: Clear identification
   - Arial sans-serif, 24px, bold
   - Amber gold color (`#fbbf24`)
   - Positioned at bottom

### Minimum Size
- Logo should not be displayed smaller than 32x32px
- For favicon, use simplified version without neural connections

### Clear Space
- Maintain minimum 10px clear space around logo on all sides
- Don't place logo on busy backgrounds that reduce visibility

## How to Generate PNG/ICO Files

### Using Inkscape (Free, Open Source)
```bash
# Install: https://inkscape.org/

# Generate PNGs
inkscape logo.svg --export-filename=logo-128.png --export-width=128 --export-height=128
inkscape logo.svg --export-filename=logo-256.png --export-width=256 --export-height=256
inkscape logo.svg --export-filename=logo-512.png --export-width=512 --export-height=512
```

### Using Online Tools
1. **PNG Conversion**: https://svgtopng.com/
2. **Favicon Generation**: https://favicon.io/ (upload PNG, generates multi-size ICO)

### Using ImageMagick (Command Line)
```bash
# Convert SVG to PNG
convert -background none logo.svg -resize 128x128 logo-128.png
convert -background none logo.svg -resize 256x256 logo-256.png
convert -background none logo.svg -resize 512x512 logo-512.png

# Create favicon.ico (multi-size)
convert logo-16.png logo-32.png logo-48.png favicon.ico
```

## Brand Personality

**LeetLog AI** combines:
- **Intelligence**: Neural network pattern, brain icon
- **Technology**: Code brackets, modern design
- **Professionalism**: Clean lines, cohesive color scheme
- **Developer-Focused**: Coding motifs, technical aesthetic

## Usage Examples

### GitHub README
```markdown
![LeetLog AI](assets/logo.svg)
# LeetLog AI
```

### HTML (Website)
```html
<img src="assets/logo.svg" alt="LeetLog AI" width="200" />
<link rel="icon" type="image/x-icon" href="/favicon.ico">
```

### Social Media
- Use `logo-512.png` for profile pictures
- Maintain deep navy blue background for brand consistency

---

**Last Updated**: May 2026  
**Created for**: GSSoC 2026 Issue #74
