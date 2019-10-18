function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}



$(function () {
    // var click=1
    $(".release_form").submit(function (e) {
        e.preventDefault()
        // if(click==1){
        //     click = 2
        //     $(".input_sub").val("确认发布")
        //     return
        // }
        // 发布新闻
        $(this).ajaxSubmit({
            beforeSubmit: function f(request){
                for(var a = 0;a<request.length;a++){
                    var item = request[a]
                    if (item['name']=='content'){
                        item['value']=tinyMCE.activeEditor.getContent()
                    }
                }
            },
            url: "/profile/news_release",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 选中索引为6的左边单菜单
                    window.parent.fnChangeMenu(6)
                    // 滚动到顶部
                    window.parent.scrollTo(0, 0)
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})

// $(function () {
//
//     $(".release_form").submit(function (e) {
//         e.preventDefault()
//
//         // TODO 发布完毕之后需要选中我的发布新闻
//         // // 选中索引为6的左边单菜单
//         // window.parent.fnChangeMenu(6)
//         // // 滚动到顶部
//         // window.parent.scrollTo(0, 0)
//     })
// })