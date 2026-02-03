import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent.parent
df = pd.read_csv(project_root / 'data' / 'processed' / 'on3_nil_rankings.csv')
print(f'Total records: {len(df)}')

# Deduplicate by name
df_unique = df.drop_duplicates(subset=['name'], keep='first')
print(f'Unique players: {len(df_unique)}')

# Save deduplicated
df_unique.to_csv(project_root / 'data' / 'processed' / 'on3_nil_rankings.csv', index=False)
print()
print('Top 15 unique players by NIL value:')
print('-' * 70)
for _, row in df_unique.nlargest(15, 'nil_valuation').iterrows():
    val = f"${row['nil_valuation']:,.0f}" if pd.notna(row['nil_valuation']) else 'N/A'
    school = row['school'][:20] if pd.notna(row['school']) else 'Unknown'
    print(f"{val:>12} | {row['name']:25} | {row['position']:4} | {school}")
