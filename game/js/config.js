/* Where the classroom server is (see server/relay.js and README "Team games at school").
   Leave empty to use PeerJS. When the game is served BY the classroom server, the server replaces this file and points
   it at itself, so nothing needs to be set. Set it only when the game lives somewhere else (GitHub Pages, itch.io) but
   should use a classroom server, e.g. 'https://spy-cadet.example.org'. A ?relay=… address in the page link wins. */
window.SC = window.SC || {};
window.SC.RELAY_URL = window.SC.RELAY_URL || '';
