import { PublicClientApplication } from "@azure/msal-browser";

const pca = new PublicClientApplication({
    auth: {
        clientId: "YOUR_CLIENT_ID"
    }
});

const loginRequest = {
    scopes: ["user.read"],
    prompt: 'select_account',
}

pca.loginPopup(loginRequest)
    .then(response => {
        // do something with the response
    })
    .catch(error => {
        // handle errors
    });