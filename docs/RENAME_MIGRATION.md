# DetectorOracle Rename Migration

This project was renamed from **IssueOracle** to **DetectorOracle**.

## Public contract

The public project identity is now:

- Repository: `bzcsk2/detectoracle-skill`
- Skill name: `detectoracle`
- User-facing invocation: `/detectoracle ...`
- Built artifact: `dist/detectoracle.skill`
- Preferred user data directory: `~/.detectoracle`
- Preferred configuration directory: `~/.config/detectoracle`
- Preferred environment variables: `DETECTORACLE_*`

## Compatibility contract

The following legacy names are intentionally still accepted during the migration window:

- Internal script path: `skills/detectoracle/scripts/issueoracle.py`
- Legacy user data directory: `~/.issueoracle`
- Legacy configuration directory: `~/.config/issueoracle`
- Legacy environment variables: `ISSUEORACLE_*`

This avoids breaking existing local installs or losing previously mined bug-experience data.

## Migration policy

1. New docs and marketplace-facing metadata should use DetectorOracle.
2. Existing users should not be forced to move data manually.
3. Internal file paths may keep `issueoracle` until a dedicated breaking migration is planned.
4. Any future full path rename should include:
   - directory move from `skills/detectoracle` to `skills/detectoracle`,
   - CLI wrapper or alias for old paths,
   - migration tests for `ISSUEORACLE_*` compatibility,
   - explicit release notes.

## Current known limitation

The Python implementation entrypoint is still named `issueoracle.py`. This is a compatibility decision, not the desired final architecture. The next hardening pass should add a first-class `detectoracle.py` entrypoint or complete the directory migration in one atomic PR.
