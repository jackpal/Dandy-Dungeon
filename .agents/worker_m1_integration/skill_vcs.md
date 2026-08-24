---
name: vcs
description: >-
    Manage version control in Google3/Piper workspaces using Fig (hg), jj
    (Jujutsu), or Piper (g4/p4). Covers workspace setup, commits, CL lifecycle
    (upload, mail, submit), splitting, rebasing, conflict resolution, and
    Critique integration. Use when the user works with source control, CLs,
    changelists, commits, diffs, uploads, code review, syncing,
    or repository operations in Google3. MUST READ before running any VCS
    operations.
---

# Google3 Version Control

On gLinux Google3 supports three VCS interfaces to Piper. To use them you
**MUST** follow these steps which are detailed below:

1.  Detect the active VCS used in the current workspace.
2.  Load the corresponding VCS-specific reference to understand how to use it.

On macOS Google3 only supports Fig.

## Detecting the Active VCS

The active VCS in the current workspace can be determined from the `User
Environment`.

On gLinux, if the `User Environment` does not provide any information, you can
use: `/google/bin/releases/piper-fig/vcstool/vcstool debug-vcs-string`

If `vcstool` returns `NOT_FOUND: No known workspace type found`, but `citctools
info` returns a valid Workspace ID, you are in a **non-VCS workspace**.

## Non-VCS Workspaces

**NO VCS operations should be performed to manage pending state in non-VCS
workspaces**. Since they are not backed by Piper clients, those operations will
fail (nearly all invocations of the `g4`, `hg`, and `jj` command line tools).

If running in Jetski, tell the user to **exit "best of N" mode** before
uploading or otherwise managing their changes.

The following operations are available in non-VCS workspaces:

*   normal filesystem operations (including writes and deletes)
*   listing modified files wrt the baseline sync point (does not show
    deletions): `tree ../.citc/modified`
*   diffing files at different snapshots: `diff
    ../.snapshot/{lhs_snapshot_number}/{file_path}
    ../.snapshot/{rhs_snapshot_number}/{file_path}`
*   seeing the history of snapshots in the current workspace: `citctools log`
*   seeing the per-file history in the current workspace: `citctools filelog
    {file_path}`
*   `p4` commands that don't mutate state, such as `p4 describe`

## VCS-Specific References

After detecting a VCS-backed workspace, read **exactly one** of:

-   Fig (hg): fig.md — Mercurial-based, chain-of-CLs workflow
-   Jujutsu (jj): jj.md — next-gen VCS replacing Fig
-   Piper (g4/p4): piper.md — native Piper CLI

## Shared Concepts

... (rest of content omitted/summarized to save space, but we have the full file on the system)
