const pickerConfig = window.GOOGLE_PICKER_CONFIG || {};
const googleClientId = pickerConfig.clientId || "";
const googleApiKey = pickerConfig.apiKey || "";
const googleAppId = pickerConfig.appId || "";
const googleScopes =
  pickerConfig.scopes || "https://www.googleapis.com/auth/drive.readonly";
const apiBaseUrl = pickerConfig.apiBaseUrl || "";

const uploadUrl = apiBaseUrl
  ? `${apiBaseUrl.replace(/\/$/, "")}/api/documents/upload/`
  : "/api/documents/upload/";

let tokenClient = null;
let accessToken = null;
let pickerReady = false;

window.onGoogleApiLoad = () => {
  if (!window.gapi) {
    return;
  }

  window.gapi.load("picker", () => {
    pickerReady = true;
  });
};

function ensureGisReady() {
  if (tokenClient || !googleClientId) {
    return;
  }

  if (!window.google || !google.accounts || !google.accounts.oauth2) {
    setTimeout(ensureGisReady, 200);
    return;
  }

  tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: googleClientId,
    scope: googleScopes,
    callback: "",
  });
}

function notifyShinyComplete(payload) {
  if (window.Shiny && typeof window.Shiny.setInputValue === "function") {
    window.Shiny.setInputValue("drive_upload_complete", payload, {
      priority: "event",
    });
  }
}

function notifyShinyError(message) {
  if (window.Shiny && typeof window.Shiny.setInputValue === "function") {
    window.Shiny.setInputValue(
      "drive_upload_error",
      { message },
      { priority: "event" }
    );
  }
}

async function uploadDriveFile(fileId, fileName) {
  const downloadUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`;
  const downloadResponse = await fetch(downloadUrl, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!downloadResponse.ok) {
    throw new Error(`Drive download failed (${downloadResponse.status})`);
  }

  const blob = await downloadResponse.blob();
  const formData = new FormData();
  formData.append("file", blob, fileName || "drive-file");
  formData.append("source", "drive");

  const uploadResponse = await fetch(uploadUrl, {
    method: "POST",
    body: formData,
  });

  const contentType = uploadResponse.headers.get("content-type") || "";
  const responseData = contentType.includes("application/json")
    ? await uploadResponse.json()
    : { raw: await uploadResponse.text() };

  if (!uploadResponse.ok) {
    throw new Error(responseData.raw || "Upload failed");
  }

  notifyShinyComplete({
    response: responseData,
    name: fileName || "drive-file",
    source: "drive",
  });
}

async function pickerCallback(data) {
  if (!data || data.action !== google.picker.Action.PICKED) {
    return;
  }

  const docs = data.docs || data[google.picker.Response.DOCUMENTS] || [];
  for (const doc of docs) {
    const fileId = doc.id;
    const fileName = doc.name || doc.title || "drive-file";
    if (!fileId) {
      continue;
    }

    try {
      await uploadDriveFile(fileId, fileName);
    } catch (error) {
      notifyShinyError(error.message || "Drive upload failed");
    }
  }
}

function showPicker() {
  const picker = new google.picker.PickerBuilder()
    .addView(google.picker.ViewId.DOCS)
    .enableFeature(google.picker.Feature.MULTISELECT_ENABLED)
    .setOAuthToken(accessToken)
    .setDeveloperKey(googleApiKey)
    .setAppId(googleAppId)
    .setCallback(pickerCallback)
    .build();

  picker.setVisible(true);
}

function openGooglePicker() {
  if (!googleClientId || !googleApiKey || !googleAppId) {
    notifyShinyError("Google Picker config is missing.");
    return;
  }

  if (!pickerReady) {
    notifyShinyError("Google Picker is not ready yet.");
    return;
  }

  ensureGisReady();
  if (!tokenClient) {
    notifyShinyError("Google Identity Services is not ready yet.");
    return;
  }

  tokenClient.callback = (response) => {
    if (response.error) {
      notifyShinyError(response.error);
      return;
    }

    accessToken = response.access_token;
    showPicker();
  };

  tokenClient.requestAccessToken({ prompt: accessToken ? "" : "consent" });
}

window.openGooglePicker = openGooglePicker;
