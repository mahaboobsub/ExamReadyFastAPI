"""
Quick verification script to check PDF inventory
"""
from pathlib import Path

PDF_DIR = Path("data/raw/cbse_class10_pdfs/maths")

# Expected PDFs
EXPECTED = {
    "real_numbers.pdf": "Real Numbers",
    "polynomials.pdf": "Polynomials",
    "PAIR OF LINEAR EQUATIONS IN TWO VARIABLES.pdf": "Pair of Linear Equations in Two Variables",
    "quadratic_equations.pdf": "Quadratic Equations",
    "SOME APPLICATIONS OF TRIGONOMETRY.pdf": "Some Applications of Trigonometry",
    "triangles.pdf": "Triangles",
    "CO-ORDINATE GEOMETRY.pdf": "Coordinate Geometry",
    "INTRODUCTION TO TRIGONOMETRY.pdf": "Introduction to Trigonometry",
    "SURFACE_AREAS_AND_VOLUMES.pdf": "Surface Areas and Volumes",
    "statistics.pdf": "Statistics",
    "probability.pdf": "Probability",
    "Full Text Book Markings and Synopsis-Class X.pdf": "Mixed Content"
}

print("="*70)
print("📚 PDF INVENTORY CHECK")
print("="*70)
print(f"Directory: {PDF_DIR.absolute()}\n")

if not PDF_DIR.exists():
    print(f"❌ Directory not found!")
    exit(1)

# Get actual PDFs
actual_pdfs = sorted(PDF_DIR.glob("*.pdf"))

print(f"✅ Found {len(actual_pdfs)} PDFs\n")

# Check each PDF
for pdf in actual_pdfs:
    size_mb = pdf.stat().st_size / (1024 * 1024)
    chapter = EXPECTED.get(pdf.name, "⚠️ UNKNOWN")
    status = "✅" if pdf.name in EXPECTED else "⚠️"
    print(f"{status} {pdf.name:<55} {size_mb:>6.2f} MB")
    print(f"   → {chapter}")

# Check for missing
print(f"\n{'='*70}")
missing = set(EXPECTED.keys()) - {p.name for p in actual_pdfs}
if missing:
    print(f"⚠️ Missing {len(missing)} PDFs:")
    for m in sorted(missing):
        print(f"   - {m}")
else:
    print(f"✅ All {len(EXPECTED)} expected PDFs present!")

print(f"\n{'='*70}")
print(f"Total Size: {sum(p.stat().st_size for p in actual_pdfs) / (1024*1024):.2f} MB")
print("="*70)
