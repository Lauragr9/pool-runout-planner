// Local/compose configuration. On Azure, the CD workflow overwrites this
// file with the deployed services' real URLs before the UI is published
// (see the deploy workflow) — this checked-in version is only for
// `docker compose up` and running the UI by hand against localhost.
window.APP_CONFIG = {
  LAYOUTS_URL: "http://localhost:8100",
  SOLVER_URL: "http://localhost:8101",
};
