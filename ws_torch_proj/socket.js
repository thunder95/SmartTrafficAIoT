
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

    this.render = function() {
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

    this.clear = function () {
        list = [];
        this.render();
    }
}
var queue = new Queue(5);

//视频配置
var video_configs = {
    "0" : ["/root/mp4s/c003.mp4", "348,364,1653,322"],
    "1" : ["/root/mp4s/rainy.mp4", "157,146,517,140"],
    "2" : ["/root/mp4s/foggy.mp4", "462,702,1028,486"],
    "3" : ["/root/mp4s/night_clip.mp4", "427,242,987,268"]
};


// send action: start play
function startPlay() {
    $("#start_btn").click(function(){
        //$("#cmd_area").html('');
	queue.clear();
        var video_id =  $("#video_src").find("option:selected").val();
        var video_src = video_configs[video_id][0];
        var entry_pts = video_configs[video_id][1];
        if (video_src != "") {
            socket.send(JSON.stringify({action: 'start', values: video_src, pts: entry_pts}));
        }
    });
}

//stop action: stop play
function stopPlay() {
    $("#stop_btn").click(function(){
        var video_id =  $("#video_src").find("option:selected").val();
        var video_src = video_configs[video_id][0];
        if (video_src != "") {
            socket.send(JSON.stringify({action: 'stop', values: video_src}));
        }
    });
}
// Get user list
function getUsers(){
    socket.send(JSON.stringify({action: 'getuser'}))
}

//create commands
function createCommand() {
     $("#create_command_btn").click(function(){
        var cmd_type =  $("#command").find("option:selected").val();
        var cmd_val = $("#command_value").val();
        console.log("create command: ", cmd_type, cmd_val);
        socket.send(JSON.stringify({action: 'command', values: cmd_val, type: cmd_type}));
    });
}


startPlay();
stopPlay();
createCommand();

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
    console.log("socket opened");
};

socket.onerror = function(){
    console.log('socket connectiong error');
};

//receive images or message from servre
var p = "";
socket.onmessage = function() {
    data = JSON.parse(event.data);
    switch (data.type) {
        case 'images':
            $("#video").attr("src", data.value);
            // console.log("received image!");
            break;
        case 'commands':
//            p = document.createElement("p");
//             console.log("received command!", data.value)
            queue.push(data.value);
            queue.render();
            break;

        case 'carNum':
            var green_t = 60 + data.value * 2;
            $("#green_time").html(green_t);
            socket.send(JSON.stringify({action: 'command', values: green_t, type: "Green_control"}));
            break;

        default:
            console.error('unsuported data', data);
    }
};
