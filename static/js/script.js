// ####################
//        EVENTS
// ####################


// Navbar toggle
$(".navbar__toggle").click(function () {
    $(".nav__mobile").slideToggle();
})

// Shows flash message
$(".flash").slideToggle();

// Hides flash message
$("#flash-close").click(function () {
    $(".flash").slideUp();
})

// Toggles password visibility
$("#pass_icon").click(passToggle);

// Toggles Dropdown items on surrender.html
$(".btn--surrender").click(function () {
    $(this).next().slideToggle();
})

// Controls image sizes to 16:9 ratio
$(window).resize(function () {
    resizeImg($(".js-img-mobile"))
    resizeImg($(".js-img-tablet-l"))
    resizeImg($(".js-img-tablet-m"))
    resizeImg($(".post__img"))
    resizeImg($(".dog__img"))
})
resizeImg($(".js-img-mobile"))
resizeImg($(".js-img-tablet-l"))
resizeImg($(".js-img-tablet-m"))
resizeImg($(".post__img"))
resizeImg($(".dog__img"))

// Back button
$(".js-btn-back").click(function () {
    window.location.href = document.referrer;
})

// Toggles post filter on post_main.html
$(".js-filter-toggle").click(
    function () {
        $(".js-form-toggle").slideToggle();
        $(".js-form-toggle").css("display", "flex")
    })


// Toggles messages/requests in inbox
$(".switch span").click(function () {
    $(this).addClass("switch-dark")
    $(this).removeClass("switch-light")
    $(this).siblings().removeClass("switch-dark")
    $(this).siblings().addClass("switch-light")
})

$(".switch__messages").click(function () {
    $("#title-messages").show();
    $(".inbox--messages").show();
    $("#title-requests").hide();
    $(".inbox--requests").hide();
})

$(".switch__requests").click(function () {
    $("#title-messages").hide();
    $(".inbox--messages").hide();
    $("#title-requests").show();
    $(".inbox--requests").show();
})

// Toggles reply message in inbox
$(document).ready(function () {
    $(".form--message").hide()
});
$(".message__reply").click(function () {
    $(".form--message").show();
    $(".message__btns").hide()
})
$(".btn--cancel").click(function () {
    $(".form--message").hide();
    $(".message__btns").show()
})

// Deletes message from inbox
$(".btn--delete").click(function () {
    disableScroll();
    $(".popup__container").css("display", "flex");
    $(".popup__text").text("You are about to delete message. Do you wish to proceed ?");
    $(`#btn-delete-confirm`).show();
    $(".btn--popup").click(function () {
        $(".popup__container").hide();
    });
    enableScroll();
})

// Changes ID of 'action' button in popup and calls popup function
$(".popup-main-btn").click(function () {
    disableScroll();
    let id = $(this).attr("id");
    switch (id) {
        case "post-edit":
            msg = "You are about to edit post. Do you wish to proceed ?";
            popUp(msg, id);
            break
        case "post-delete":
            msg = "You are about to delete post. Do you wish to proceed ?";
            popUp(msg, id);
            break
        case "dog-edit":
            msg = "You are about to edit info for this dog. Do you wish to proceed ?";
            popUp(msg, id);
            break
        case "dog-delete":
            msg = "You are about to remove this dog from the database. Do you wish to proceed ?";
            popUp(msg, id);
            break
    }
})

// Changes text for 'upload photo' button
$(".inputfile").change(function (e) {
    fileDefault = "No file selected";
    fileSelected = e.target.value.split('\\').pop();
    if (fileSelected === "") {
        $(".js-btn-photo span").text(" " + fileDefault)
        $(".js-btn-photo i").removeClass("fas fa-check")
        $(".js-btn-photo i").addClass("fas fa-upload")
    } else {
        $(".js-btn-photo span").text(" " + fileSelected)
        $(".js-btn-photo i").removeClass("fas fa-upload")
        $(".js-btn-photo i").addClass("fas fa-check")
    }
})

// Gets values from local storage and fills in the form
// This is used to keep the previous user values on form refresh
// in case of error
$(document).on('click', '#flash-back-register', getLocalRegister)
$(document).on('click', '#flash-back-post', getLocalPost)
$(document).on('click', '#flash-back-dog', getLocalDog)

// Compares highest previous position of scroll bar with current position of scroll bar and dependion on the outcome decides if user is scrolling up or down. Since this is mainly mobile functionality and on some phones it is possible to scrol even further the max height of the screen, function needs to compensate this with 80px on top and calculate scrollLimit on the bottom.
let scrollTop = -1; 
let scrollCurrent;
let containerHeight = $(".main-container").height()
let bodyHeight = $("body").height()
let scrollLimit = containerHeight - bodyHeight
$(window).scroll(function() {
    // Hides navbar only if page is higher than screen height
    if (scrollLimit > 0) {
        scrollCurrent = $(window).scrollTop();
        if (scrollCurrent >= scrollTop && scrollCurrent > 80) {
            $(".nav").css("top", "-80px");
        } else if (scrollCurrent > scrollLimit) {
            $(".nav").css("top", "-80px");
        } else {
            $(".nav").css("top", "0");
        }
        scrollTop = scrollCurrent;
    }
})


// ####################
//      FUNCTIONS
// ####################


// Enables scrolling on the page
function enableScroll() {
    $('html, body').css({
        "overflow": "visible",
    });
}

// Disables scrolling on the page
function disableScroll() {
    $('html, body').css({
        "overflow": "hidden",
    });
}

// Toggles password visibility
function passToggle() {
    let pass = $("#password")[0]
    if (pass.type === "password") {
        pass.type = "text";
        $("#password").css({
            "font-weight": "400",
            "letter-spacing": "0"
        });
        $("#pass_icon").removeClass("fa-eye");
        $("#pass_icon").addClass("fa-eye-slash");
        $("#pass_toggle").text("Hide password");
    } else {
        pass.type = "password";
        $("#password").css({
            "font-weight": "900",
            "letter-spacing": "3px"
        });
        $("#pass_icon").removeClass("fa-eye-slash");
        $("#pass_icon").addClass("fa-eye");
        $("#pass_toggle").text("Show password");
    }
}

// Controls image sizes to 16:9 ratio
function resizeImg(img) {
    width = img.width()
    height = width * 0.5625
    img.css("height", `${height}px`);
}

// Toggles popup message
let msg;

function popUp(msg, id) {
    $(".popup__container").css("display", "flex");
    $(".popup__text").text(msg);
    $(`#${id}-confirm`).show();
    $(".btn--popup").click(function () {
        $(".popup__container").hide();
        $(`#${id}-confirm`).hide();
    });
    enableScroll();
};

// Saves values from form to local storage
function setLocalRegister() {
    localStorage.setItem("origin", "register")
    localStorage.setItem("username", $("#username").val())
    localStorage.setItem("email", $("#email").val())
    localStorage.setItem("fname", $("#fname").val())
    localStorage.setItem("lname", $("#lname").val())
    localStorage.setItem("phone", $("#phone").val())
    localStorage.setItem("about", $("#about").val())
}

// Gets values from local storage and fills in the form
function getLocalRegister() {
    $("#username").val(localStorage.getItem("username"))
    $("#email").val(localStorage.getItem("email"))
    $("#fname").val(localStorage.getItem("fname"))
    $("#lname").val(localStorage.getItem("lname"))
    $("#phone").val(localStorage.getItem("phone"))
    $("#about").val(localStorage.getItem("about"))
    $(".flash__container").hide();
    localStorage.clear();
}

// Saves values from form to local storage
function setLocalPost() {
    localStorage.setItem("origin", "post")
    localStorage.setItem("category", $("#category").val())
    localStorage.setItem("title", $("#title").val())
    localStorage.setItem("summary", $("#summary").val())
    localStorage.setItem("content", $("#content").val())
}

// Gets values from local storage and fills in the form
function getLocalPost() {
    $("#category").val(localStorage.getItem("category"))
    $("#title").val(localStorage.getItem("title"))
    $("#summary").val(localStorage.getItem("summary"))
    $("#content").val(localStorage.getItem("content"))
    $(".flash__container").hide();
    localStorage.clear();
}

// Saves values from form to local storage
function setLocalDog() {
    localStorage.setItem("origin", "dog")
    localStorage.setItem("name", $("#name").val())
    localStorage.setItem("gender", $("#gender").val())
    localStorage.setItem("age", $("#age").val())
    localStorage.setItem("size", $("#size").val())
    localStorage.setItem("greeting", $("#greeting").val())
    localStorage.setItem("description", $("#description").val())
    // Stores checkbox values in local storage
    // CODE CREDIT: https://stackoverflow.com/a/590040
    let goodWith = []
    $(".js-good_with:checked").each(function () {
        goodWith.push($(this).val());
    });
    localStorage.setItem("good_with", goodWith)
}

// Gets values from local storage and fills in the form
function getLocalDog() {
    $("#name").val(localStorage.getItem("name"))
    $("#gender").val(localStorage.getItem("gender"))
    $("#age").val(localStorage.getItem("age"))
    $("#size").val(localStorage.getItem("size"))
    $("#greeting").val(localStorage.getItem("greeting"))
    $("#description").val(localStorage.getItem("description"))
    // Values of checked boxes are put in array
    let goodWith = localStorage.getItem("good_with").split(',');
    // Compares values of all checkboxes with values of checked ones. If match then marks them as checked again
    // CODE CREDIT: https://learn.jquery.com/using-jquery-core/faq/how-do-i-check-uncheck-a-checkbox-input-or-radio-button/
    i = 0
    $(".js-good_with").each(function () {
        if ($(this).val() === goodWith[i]) {
            $(this).prop("checked", true);
            i++
        } else {
            $(this).prop("checked", false);
        }
    });
    $(".flash__container").hide();
    localStorage.clear();
}