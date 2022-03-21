
var socket = new WebSocket("ws://127.0.0.1:5678");

function Queue(size) {
    var list = [];

    //向队列中添加数据
    this.push = function(data) {
        if (data==null) {
            return false;
        }
        //如果传递了size参数就设置了队列的大小
        if (size != null && !isNaN(size)) {
            if (list.length == size) {
                this.pop();
            }
        }
        list.unshift(data);
        return true;
    }

    //从队列中取出数据
    this.pop = function() {
        return list.pop();
    }

    this.render = function {
       var content = list.join("\n");
       $('#cmd_area').html(content);
    }

    //返回队列的大小
    this.size = function() {
        return list.length;
    }

    //返回队列的内容
    this.quere = function() {
        return list;
    }
}
var queue = new Queue(3);

// send action: start play
function startPlay() {
    $("#start_btn").click(function(){
        var video_src = $("#video_src").val();
        console.log("video_src", video_src);
        if (video_src != "") {
            socket.send(JSON.stringify({action: 'start', values: video_src}));
        }
    });
}

//stop action: stop play
function stopPlay() {
    $("#stop_btn").click(function(){
        var video_src = $("#video_src").val();
        if (video_src != "") {
            socket.send(JSON.stringify({action: 'stop', values: video_src}));
        }
    });
}
// Get user list
function getUsers(){
    socket.send(JSON.stringify({action: 'getuser'}))
}


startPlay();
stopPlay();

socket.onopen = function(){
//    text_area.addEventListener('keyup', function(e){
//        if(e.keyCode === 13){
//            if(this.value.trim() === ""){
//                return false;
//            }
//
//            socket.send(JSON.stringify({action: 'messages', values: this.value.trim()}));
//            this.value = "";
//        }
//    });
};

socket.onerror = function(){
    console.log('socket connectiong error');
};

//receive images or message from servre
var p = "";
socket.onmessage = function() {

    data = JSON.parse(event.data);
    console.log(data)
    switch (data.type) {
        case 'images':
            $("#video").attr("src", data.value);
            console.log("received image!");
            break;
        case 'command':
//            p = document.createElement("p");
            console.log("received command!")
            /*
                queue.push(data.value)
                queue.render();
            */
            break;
        default:
            console.error('unsuported data', data);
    }
};
