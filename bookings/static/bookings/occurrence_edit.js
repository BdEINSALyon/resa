$('document').ready(function () {
    var options = {
        valueNames: ['name', 'category']
    };

    new List('resources', options);

    $('#search').keypress(function (e) {
        if (e.which == 13) {
            e.preventDefault();
        }
    });
});


