# Tasks: UV Package Management Migration

**Input**: Design documents from `/Users/edanker/development/dankerchat/specs/002-uv-migration/`  
**Prerequisites**: plan.md (✓), research.md (✓), migration-guide.md (✓), quickstart.md (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → migration-guide.md: Extract migration steps → migration tasks
   → research.md: Extract decisions → setup and validation tasks
   → quickstart.md: Extract test scenarios → verification tasks
3. Generate tasks by category:
   → Setup: backup, safety, uv installation
   → Migration: configuration, dependency conversion
   → Testing: verification, validation, rollback testing
   → Documentation: updates, guides, CI/CD
   → Cleanup: remove old files, final verification
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All migration steps covered?
   → Rollback procedures tested?
   → Documentation updated?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
Based on plan.md: Web application structure with tooling changes
- **Root files**: `pyproject.toml`, `uv.lock`, `requirements.txt` (deprecated)
- **Documentation**: `README.md`, `specs/`, `CLAUDE.md`
- **Scripts**: `scripts/` directory updates
- **CI/CD**: `.github/workflows/` updates

## Phase 3.1: Safety & Backup
- [ ] T001 [P] Create backup of current requirements in `backup-requirements.txt`
- [ ] T002 [P] Create backup of current scripts in `scripts-backup/` directory
- [ ] T003 [P] Document current Python environment in `environment-snapshot.txt`
- [ ] T004 Commit all current changes with message "Pre-UV migration snapshot"

## Phase 3.2: UV Installation & Verification ⚠️ TESTS FIRST
**CRITICAL: These verification tests MUST be written and MUST FAIL before UV implementation**
- [ ] T005 [P] Create UV installation test in `tests/migration/test_uv_install.py`
- [ ] T006 [P] Create pyproject.toml validation test in `tests/migration/test_pyproject_config.py`
- [ ] T007 [P] Create dependency sync test in `tests/migration/test_dependency_sync.py`
- [ ] T008 [P] Create cross-platform compatibility test in `tests/migration/test_cross_platform.py`
- [ ] T009 Run migration tests to confirm they FAIL (RED phase)

## Phase 3.3: Core Migration (ONLY after tests are failing)
- [ ] T010 Install UV package manager following research.md installation guide
- [ ] T011 Create initial `pyproject.toml` with project metadata and dependencies
- [ ] T012 Convert requirements.txt dependencies to pyproject.toml format
- [ ] T013 Generate `uv.lock` file with locked dependency versions
- [ ] T014 Create UV development environment with `uv sync`

## Phase 3.4: Verification & Testing  
- [ ] T015 Verify UV environment creation speed (<15 seconds target)
- [ ] T016 Test dependency installation with existing project dependencies
- [ ] T017 Verify Python version compatibility (3.11+)
- [ ] T018 Test UV commands: `uv run python`, `uv run pytest`, `uv shell`
- [ ] T019 Run existing project tests with UV environment
- [ ] T020 Verify migration tests now PASS (GREEN phase)

## Phase 3.5: Scripts & Configuration Updates
- [ ] T021 [P] Update `scripts/setup.sh` to use UV commands instead of venv
- [ ] T022 [P] Update development scripts to use `uv run` prefix
- [ ] T023 [P] Create UV-specific helper scripts in `scripts/uv-helpers.sh`
- [ ] T024 Update `.gitignore` to include `.venv/` and `uv.lock`
- [ ] T025 [P] Update environment variable handling for UV workflows

## Phase 3.6: Documentation Updates
- [ ] T026 [P] Update `README.md` setup section with UV installation instructions
- [ ] T027 [P] Update `CLAUDE.md` with UV-specific development commands
- [ ] T028 [P] Create migration announcement in `MIGRATION-NOTICE.md`
- [ ] T029 Update project documentation references from pip/venv to UV

## Phase 3.7: CI/CD Migration
- [ ] T030 Create new GitHub Actions workflow in `.github/workflows/ci-uv.yml`
- [ ] T031 Update existing workflow to use `astral-sh/setup-uv@v3` action
- [ ] T032 Replace pip commands with UV equivalents in CI configuration
- [ ] T033 Test CI/CD pipeline with UV-based builds
- [ ] T034 Verify CI build performance improvement (target: 3-5x faster)

## Phase 3.8: Rollback Testing
- [ ] T035 [P] Test rollback procedure following `rollback-guide.md`
- [ ] T036 [P] Verify rollback scripts work on clean environment
- [ ] T037 [P] Test migration → rollback → re-migration cycle
- [ ] T038 Document any rollback issues and solutions

## Phase 3.9: Team Migration & Polish  
- [ ] T039 [P] Create team migration checklist in `docs/team-migration.md`
- [ ] T040 [P] Update developer onboarding guide with UV instructions
- [ ] T041 Test migration guide with fresh developer setup
- [ ] T042 Measure and document performance improvements
- [ ] T043 [P] Clean up deprecated `requirements.txt` files (after verification)
- [ ] T044 [P] Remove old venv-related scripts and documentation

## Phase 3.10: Final Validation
- [ ] T045 Run complete test suite with UV environment
- [ ] T046 Verify all development workflows function correctly
- [ ] T047 Performance benchmark: compare setup times (venv vs UV)  
- [ ] T048 Team review: collect feedback on migration process
- [ ] T049 Update project version to 0.1.1 (BUILD increment for tooling change)
- [ ] T050 Final commit with migration completion message

## Dependencies
- Safety tasks (T001-T004) before migration tests
- Migration tests (T005-T009) before implementation (T010-T014)
- T010 (UV installation) blocks T011-T014
- T011 (pyproject.toml) blocks T012-T013
- T015-T020 (verification) before scripts updates (T021-T025)
- Documentation (T026-T029) can run parallel with CI/CD (T030-T034)
- T043-T044 (cleanup) only after T045-T046 (final validation)

## Parallel Execution Examples

### Phase 1: Safety Backup (T001-T003)
```bash
# Launch backup tasks together:
Task: "Create backup of current requirements in backup-requirements.txt"
Task: "Create backup of current scripts in scripts-backup/ directory"  
Task: "Document current Python environment in environment-snapshot.txt"
```

### Phase 2: Migration Tests (T005-T008)
```bash
# Launch test creation together:
Task: "Create UV installation test in tests/migration/test_uv_install.py"
Task: "Create pyproject.toml validation test in tests/migration/test_pyproject_config.py"
Task: "Create dependency sync test in tests/migration/test_dependency_sync.py"
Task: "Create cross-platform compatibility test in tests/migration/test_cross_platform.py"
```

### Phase 5: Scripts Updates (T021-T025)
```bash
# Launch script updates together:
Task: "Update scripts/setup.sh to use UV commands instead of venv"
Task: "Update development scripts to use uv run prefix"
Task: "Create UV-specific helper scripts in scripts/uv-helpers.sh"
Task: "Update environment variable handling for UV workflows"
```

### Phase 6: Documentation (T026-T029)
```bash
# Launch documentation updates together:
Task: "Update README.md setup section with UV installation instructions"
Task: "Update CLAUDE.md with UV-specific development commands"  
Task: "Create migration announcement in MIGRATION-NOTICE.md"
```

## Migration-Specific Notes
- **TDD Approach**: Migration tests verify UV functionality before implementation
- **Safety First**: All backup tasks complete before any migration changes
- **Performance Focus**: Track speed improvements throughout migration
- **Rollback Ready**: Test rollback procedures before team deployment
- **Team Communication**: Document changes and provide clear migration path

## Validation Checklist
*GATE: Checked before task completion*

- [x] All migration steps from research.md covered
- [x] All backup procedures included
- [x] Tests come before implementation (TDD)
- [x] Parallel tasks truly independent  
- [x] Each task specifies exact file path
- [x] Rollback procedures tested
- [x] Performance benchmarking included
- [x] Documentation updates comprehensive
- [x] CI/CD migration covered
- [x] Team migration process documented

## Success Criteria
- UV environment setup <15 seconds (vs 45-120s with venv)
- All existing functionality preserved
- CI/CD pipeline 3-5x faster
- Team can migrate following documentation
- Rollback procedures verified and documented
- Project version incremented to reflect tooling change