// VoiceOfOpenDoor - focus management and button-based internal navigation.
//
// FOCUS MANAGEMENT
// After an action (save, delete, etc.) the server redirects to a page
// with an element carrying tabindex="-1" - either #status-message
// (a confirmation of what just happened) or #confirm-heading (the
// delete confirmation page's heading). Move keyboard/screen-reader
// focus there on load, rather than leaving it at the top of the page.
//
// Dean reported (July 29, 2026) that focus was jumping to the top of
// the page instead of landing on the status message. Root cause: on a
// full page navigation, JAWS resets its own virtual cursor to the top
// of the document and starts reading from there - a script-set
// .focus() call on DOMContentLoaded can lose that race, because JAWS
// may not have finished initializing its virtual buffer for the new
// page yet. Fix: wait for the later `load` event (page fully loaded,
// including images/audio) and add a short delay before calling
// .focus(), giving JAWS more time to finish initializing first. This
// is a known, documented race condition in screen reader focus
// management, not something a single instant fix eliminates for
// certain - if this is still unreliable after retesting, the delay
// may need to be longer, or a different technique may be needed.
window.addEventListener("load", function () {
    setTimeout(function () {
        var target = document.getElementById("status-message") || document.getElementById("confirm-heading");
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
