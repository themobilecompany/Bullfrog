// APS
// Submit post on submit
$('.aps_update_form').on('submit', function(event){
    event.preventDefault();
    post_form($(this));
});
// Submit post and remove styling on blur
$('.aps_update_form input[name=attention_points]').on('blur', function(event){
    if(event.relatedTarget && event.relatedTarget.type!="submit"){
        post_form($(this).closest('form'));
     }
    $(this).removeClass('editmode');
});
// Add styling on focus
$('.aps_update_form input[name=attention_points]').on('focus', function(event){
    $(this).addClass('editmode');
});


// AJAX for posting
function post_form($form) {
    // get a jquery reference for the input fields we want to post
    var $input_aps  = $form.find('input[name=attention_points]');
    // clean the APS value before processing
    var clean_aps = $input_aps.val().replace(",",".");
    //  form security token
    var $input_csrf = $form.find('input[name=csrfmiddlewaretoken]');
    // alter the post url so it returns json after update is done
    var post_url = $form.attr('action');
    post_url = post_url + '?output=json';
    // disable the input field, to signal that ajax call is in progress
    $input_aps.attr('disabled','disabled');

    // Only proceed if clean_aps is a valid number
    if (isNaN(parseFloat(clean_aps)) && !isFinite(clean_aps) || !$.isNumeric(clean_aps) || clean_aps < 0) {
        invalidInput($input_aps)
    } else {
        $.ajax({
            url : post_url,
            type : $form.attr('method'), // http method
            data : {                     // data sent with the post request
                attention_points    : clean_aps,
                csrfmiddlewaretoken : $input_csrf.val(),
            },
            // handle a successful response
            success : function(json) {
                $input_aps.removeAttr('disabled');

                if (parseFloat(clean_aps) == 0) {
                    // We want to allow the user to set 0 APs, but also highlight when that is done
                    invalidInput($input_aps)
                } else {
                    // remove row, when inside action box
                    if($input_aps.closest('div.action').length){ //if the input lives inside an action box
                        $input_aps.closest('tr').hide();
                        // hide action box if all rows are hidden:
                        if($input_aps.closest('table').find('tr.action:visible').length == 0) {
                            $input_aps.closest('div.action').hide();
                            $('#no_action_items_placeholder').show();
                        }
                    }else{
                        // remove styling from row
                        $input_aps.closest('tr').removeClass('action');
                    }
                }
                updateTotals(json, $input_aps)
            },
            // handle a non-successful response
            error : function(xhr,errmsg,err) {
                invalidInput($input_aps)
                console.log(xhr.status + ": " + xhr.responseText)
                console.log(errmsg + ": " + err)
            }
        });
    }
};

// DELETING
$('.aps_delete').on('submit', function(event){
    event.preventDefault();
    post_delete_form($(this));
})

function post_delete_form($form) {
    var $delete  = $form.find('input[name=delete]');
    //  form security token
    var $input_csrf = $form.find('input[name=csrfmiddlewaretoken]');
    // alter the post url so it returns json after update is done
    var post_url = $form.attr('action');
//    post_url = post_url + '?output=json';

    $.ajax({
        url : post_url,
        type : $form.attr('method'), // http method
        data : {                     // data sent with the post request
            csrfmiddlewaretoken : $input_csrf.val(),
        },
        // handle a successful response
        success : function(json) {

            // remove row, when inside action box
            $delete.closest('tr').hide();
            // hide action box if all rows are hidden:
            if($delete.closest('table').find('tr.deleted:visible').length == 0) {
                $delete.closest('div.action').hide();
                $('#no_action_items_placeholder').show();
            }
//            updateTotals(json, $delete)
        },
        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    })
}

function invalidInput(formField) {
    formField.closest('tr').addClass('action');
    formField.fadeIn(200).fadeOut(200).fadeIn(200).fadeOut(200).fadeIn(200);
    formField.removeAttr('disabled');
}

function updateTotals(json, formElement) {
    // update totals
    try{
        // preserve newlines, etc - use valid JSON
        json = json.replace(/\\n/g, "\\n")
               .replace(/\\'/g, "\\'")
               .replace(/\\"/g, '\\"')
               .replace(/\\&/g, "\\&")
               .replace(/\\r/g, "\\r")
               .replace(/\\t/g, "\\t")
               .replace(/\\b/g, "\\b")
               .replace(/\\f/g, "\\f")
        // remove non-printable and other non-valid JSON chars
        json = json.replace(/[\u0000-\u0019]+/g,"")
        json = json.replace(/[\u003C]+/g,"")
        var responseObj = JSON.parse(json)
    }catch(err){
        console.log('Invalid JSON response')
        console.log(err)
    }
    // remove current total values, they need to be updated by the json response
    var refreshLink = '<a href="javascript:location.reload()">?</a>';
    // Rolefiller Lists
    $('#rolefiller_list_total').html(refreshLink);
    // Circle Lists
    $('#circle_list_granted').html(refreshLink);
    $('#circle_list_balance').html(refreshLink);
    formElement.closest('tr').find('td.balance').html(refreshLink);
    // Circle Detail overview
    $('#circle_detail_assigned_to_rolefillers').html(refreshLink);
    $('#circle_detail_assigned').html(refreshLink);
    $('#circle_detail_balance').html(refreshLink);

    // Try to update the totals. Using Try/Catch because response objects are not generic for each page this script runs on. Properties dont always exist.

    // Rolefiller Lists
    try{
        $('#rolefiller_list_total').text(responseObj.circle_details.rolefillers.rolefiller_list_total);
    }catch(err){}

    // Circle Lists
    try{
        $('#circle_list_granted').text(responseObj.circle_details.subcircles.circle_list_totals.circle_list_granted);
    }catch(err){}
    try{
        $('#circle_list_balance').text(responseObj.circle_details.subcircles.circle_list_totals.circle_list_balance);
    }catch(err){}

    // Circle Detail overview
    try{
        $('#circle_detail_assigned_to_rolefillers').text(responseObj.circle_details.subcircles_rolefillers_total);
    }catch(err){}
    try{
        $('#circle_detail_assigned').text(responseObj.circle_details.attention_points_assigned);
    }catch(err){}
    try{
        $('#circle_detail_balance').text(responseObj.circle_details.attention_points_balance);
    }catch(err){}
}