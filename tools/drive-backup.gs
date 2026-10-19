// PMc apps — Google Drive backup script.
// Saves each app's progress to Drive and hands it back for restore.
// Files go to: My Drive / Welsh / Gramadeg backups (other apps get their own folder under PMc app backups).
//   <app>-latest.json        overwritten on every save
//   <app>-YYYY-MM-DD.json    one per day, so a bad save never wipes history

const FOLDERS = {
  gramadeg: ['Welsh', 'Gramadeg backups'],
};
const DEFAULT_PATH = ['PMc app backups'];

function folderFor_(app) {
  const path = (FOLDERS[app] || DEFAULT_PATH.concat([app]));
  let f = DriveApp.getRootFolder();
  path.forEach(function (name) {
    const it = f.getFoldersByName(name);
    f = it.hasNext() ? it.next() : f.createFolder(name);
  });
  return f;
}

function put_(folder, name, text) {
  const it = folder.getFilesByName(name);
  if (it.hasNext()) it.next().setContent(text);
  else folder.createFile(name, text, 'application/json');
}

function appName_(e) {
  return String((e.parameter && e.parameter.app) || 'gramadeg').replace(/[^a-z0-9-]/gi, '').toLowerCase() || 'gramadeg';
}

function doPost(e) {
  const app = appName_(e);
  const body = e.postData.contents;
  JSON.parse(body); // refuse anything that isn't valid JSON
  const f = folderFor_(app);
  const day = Utilities.formatDate(new Date(), 'Europe/London', 'yyyy-MM-dd');
  put_(f, app + '-latest.json', body);
  put_(f, app + '-' + day + '.json', body);
  return out_({ ok: true, saved: day });
}

function doGet(e) {
  const app = appName_(e);
  const it = folderFor_(app).getFilesByName(app + '-latest.json');
  return out_({ ok: true, data: it.hasNext() ? JSON.parse(it.next().getBlob().getDataAsString()) : null });
}

function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
