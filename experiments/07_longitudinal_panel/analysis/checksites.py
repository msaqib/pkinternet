import pandas as pd

targets = pd.read_csv('/mnt/user-data/uploads/targets.csv')
candidates = pd.read_csv('/mnt/user-data/uploads/site_candidates_cisa.csv')

merged = targets.merge(candidates[['website','cisa_sector']], 
                       left_on='target', right_on='website', how='left')

print("Per sector breakdown:")
print(merged.groupby(['cisa_sector','class']).size().unstack(fill_value=0))
print(f"\nTotal PK pool in candidates: {len(candidates[candidates['hosting']=='Pakistani'])}")
print(f"Total CDN pool in candidates: {len(candidates[candidates['hosting']=='CDN'])}")
print(f"Total Abroad pool in candidates: {len(candidates[candidates['hosting']=='Abroad'])}")