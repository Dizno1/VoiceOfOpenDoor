// VoiceOfOpenDoor - centralized focus management and button-based
// internal navigation.
//
// FOCUS MANAGEMENT - ONE system, not one script per template.
//
// Every page has exactly one intended focus target, decided
// server-side and expressed as one of two element IDs:
//
//   #page-focus-target - the specific result of a completed action
//     (a status message, a results heading, an error summary). Used
//     when a page's H1 alone wouldn't convey what just happened -
//     e.g. Home after a classification save, Recordings after a
//     delete. Always carries tabindex="-1".
//
//   #page-heading - the page's own H1. Present and tabbable on every
//     page, always tabindex="-1". This is the correct target for
//     ordinary navigation (Home to Recordings, Recordings to a
//     recording's detail page, etc.) and is also the fallback if a
//     page was supposed to set #page-focus-target but didn't.
//
// On load, focus #page-focus-target if present, otherwise
// #page-heading. Never the body, main, skip link, nav, or Home
// button - those are not legitimate programmatic focus targets per
// the project's accessibility requirements.
//
// Runs once on the `load` event (not DOMContentLoaded), with a short
// delay - this is the ONE place that delay exists, replacing several
// per-template versions that used to compete with each other. JAWS
// can reset its own virtual cursor to the top of a new page on
// navigation; `load` plus a short delay gives it time to finish
// before this script's explicit .focus() call runs, rather than
// racing it on DOMContentLoaded.
//
// This only runs once per real page load. It does not re-fire while
// the user is moving the JAWS virtual cursor through an
// already-loaded page, and it never runs during an in-progress
// action (every action in this app is a normal server round trip,
// not a partial in-page update, so there is no "still working"
// state for this script to accidentally interrupt).
window.addEventListener("load", function () {
    setTimeout(function () {
        var target = document.getElementById("page-focus-target") || document.getElementById("page-heading");
        if (target) {
            target.focus();
        }
    }, 150);
});

// BUTTON-BASED INTERNAL NAVIGATION
// Elements with class "as-link" and a data-href attribute are <button>
// elements that navigate like a link, without being one. Dean's
// direction (July 29, 2026): with many same-purpose internal links
// (e.g. a 19-recording list), JAWS's link-specific quick navigation
// (U for unvisited, V for visited) gets cluttered with entries that
// don't meaningfully differ by visited state. Buttons remove them
// from that quick-nav entirely while remaining fully keyboard
// operable (native <button> already responds to Enter and Space).
// True navigation (browser back/forward, address bar) still works
// normally, since this still sets window.location.href.
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".as-link[data-href]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            window.location.href = btn.getAttribute("data-href");
        });
    });
});
