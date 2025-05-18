import sys

def count_loc_all(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    return sum(
        1 for line in lines
        if line.strip()
        and not line.strip().startswith('#')
        and not line.strip().startswith('import')
        and not line.strip().startswith('from ')
    )

def count_loc_without_folds_etc(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    loc = 0
    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith('#') or \
           stripped.startswith('import') or stripped.startswith('from '):
            continue

        if (stripped.startswith('Requires(state_pred') or
            stripped.startswith('Requires(self.state')):
            loc -= 1 
        elif stripped.startswith('Unfold') or stripped.startswith('Fold'):
            continue
        else:
            loc += 1

    return loc

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python count_loc.py <file.py>")
        sys.exit(1)

    file_path = sys.argv[1]
    all_loc = count_loc_all(file_path)
    loc_without_folds = count_loc_without_folds_etc(file_path)
    print("# Usability:")
    print(f"# All LOC: {all_loc}")
    print(f"# Without state/folding LOC: {loc_without_folds}")
    print(f"# Factor: {all_loc / loc_without_folds}")