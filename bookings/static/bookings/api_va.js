$('document').ready(function () {
    $('#va_form').on('submit', function() {
        var va_button = $('#va_button');
        var old_text = va_button.text();
        va_button.attr('disabled', 'disabled');
        va_button.text('Chargement...');

        var va_card = $('#va_card_input').val();
        $.getJSON('/book/api/va/' + va_card, function(student) {
            $('#id_contact_first_name').val(student.first_name);
            $('#id_contact_last_name').val(student.last_name);
            $('#id_contact_email').val(student.email);
            $('#id_contact_phone').val(student.phone);
            va_button.text(old_text);
            va_button.removeAttr('disabled');
        })
    })
});