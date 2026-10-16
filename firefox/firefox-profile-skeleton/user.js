// Pedrozilla 2.x - preferencias del perfil (motor Gecko / Firefox).
//
// Este archivo es una PLANTILLA: el instalador y el lanzador la copian al
// perfil real (%APPDATA%\pedrozilla\firefox-profile en Windows,
// ~/.config/pedrozilla/firefox-profile en Linux) sustituyendo
// __PEDROZILLA_NEWTAB_URL__ por la pagina local de nueva pestana.
// Para regenerarlo desde cero, borra la carpeta del perfil.
//
// No requiere permisos de administrador: todo vive en el perfil.

user_pref("browser.startup.homepage", "__PEDROZILLA_NEWTAB_URL__");
user_pref("browser.startup.page", 1);
user_pref("browser.toolbars.bookmarks.visibility", "always");
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);
user_pref("browser.search.defaultenginename", "DuckDuckGo");
user_pref("browser.search.order.1", "DuckDuckGo");
user_pref("extensions.pocket.enabled", false);
user_pref("browser.newtabpage.activity-stream.showSearch", true);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
