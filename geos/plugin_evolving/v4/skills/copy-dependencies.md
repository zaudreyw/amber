---
name: copy-dependencies
description: How to identify and copy all external files referenced by a GEOS XML base file
---
## Detailed instructions

1. **Identify base file directory**: Determine the full path of the base XML file (e.g., `/geos_lib/inputFiles/poromechanics/<file>`). Its directory is `dirname /geos_lib/inputFiles/poromechanics/<file>` → `/geos_lib/inputFiles/poromechanics/`.

2. **List all files in that directory**: Run `ls -la <directory>` to see all sibling files. Note any:
   - `.geos`, `.txt`, `.csv` files (table data)
   - Other `.xml` files that might be included
   - Subdirectories (e.g., `tables/`, `scripts/`)

3. **Search for includes in the base file**: Grep the base file for `<Included>` or `FilePath` patterns. Example: `grep -n 'Included\|File\|\.geos\|\.txt\|\.csv' <base_file>`. This reveals every external dependency.

4. **Create corresponding subdirectories in workspace**: If the base file references `tables/time.geos`, create `mkdir -p /workspace/inputs/tables/` (same relative path as in the base file).

5. **Copy all dependencies**: For each referenced file, use `cp <source> <dest>`. Example: `cp /geos_lib/inputFiles/poromechanics/tables/*.geos /workspace/inputs/tables/`.

6. **Verify**: Run `find /workspace/inputs -type f | sort` to list all files. Then re-grep the base file for any unresolved references (paths that don't exist in your workspace).

7. **Included XML files**: If the base file includes another XML, copy that file and repeat steps 2–5 for it (it may have its own dependencies).
