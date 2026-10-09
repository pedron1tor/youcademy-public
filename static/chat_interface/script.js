// Creating a WebSocket connection
var chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/'
);

chatSocket.onmessage = function(e) {
    var data = JSON.parse(e.data);
    var message = data.message;
    document.querySelector('#messages').innerHTML += ('<li>' + message + '</li>');
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

document.querySelector('#messageInput').focus();
document.querySelector('#messageInput').onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('button').click();
    }
};

function sendMessage() {
    var messageInputDom = document.querySelector('#messageInput');
    var message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
        'message': message
    }));
    messageInputDom.value = '';
}