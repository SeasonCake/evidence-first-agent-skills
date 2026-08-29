# Attribution

Inspired by the MIT-licensed `check-agent-compatibility` skill in Cursor's official
plugins repository. This rewrite replaces parallel scoring with sequential evidence
surfaces and adds endpoint continuity, runtime-vs-authorization separation, stale job
recovery, staged-file checks, and Git-index/fresh-clone truth. See `UPSTREAM.md`.

Project origin: BidKing successor work exposed failures caused by long histories, stale
handles, and incomplete tracked recovery inputs. The public companion is
[`bidking-inference`](https://github.com/SeasonCake/bidking-inference).
