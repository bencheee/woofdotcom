// Navbar toggle
$(".navbar__toggle").click(function () {
    $(".nav__mobile").slideToggle();
})

// Shows flash message
$(".flash").slideToggle();

// Hides flash message
$("#flash-close").click(function(){
    $(".flash").slideUp();
})
