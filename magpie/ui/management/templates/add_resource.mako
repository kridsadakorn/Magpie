<%inherit file="ui.home:templates/template.mako"/>

<%block name="breadcrumb">
<li><a href="${request.route_url('home')}">
    Home</a></li>
<li><a href="${request.route_url('view_services', cur_svc_type=cur_svc_type)}">
    Services</a></li>
<li><a href="${request.route_url('edit_service', service_name=service_name, cur_svc_type=cur_svc_type)}">
    Service [${service_name}]</a></li>
<li><a href="${request.route_url('add_resource', service_name=service_name, cur_svc_type=cur_svc_type, resource_id=resource_id)}">
    Add Resource</a></li>
</%block>

<h1>New Resource</h1>

<form class="new_item_form" id="add_resource_form" action="${request.path}" method="post">
    <table class="fields_table">
        <tr>
            <td>Resource name:</td>
            <td>
                <div class="input_container"><label>
                    <input type="text" value="" name="resource_name" class="equal_width">
                </label></div>
            </td>
        </tr>
        <tr>
            <td>Resource type:</td>
            <td><label>
                <div class="input_container">
                    <select name="resource_type" class="equal_width">
                        %for res_type in cur_svc_res:
                            <option value="${res_type}">${res_type}</option>
                        %endfor
                    </select>
                </div>
            </label></td>
        </tr>
        <tr><td class="centered" colspan="2"><input type="submit" value="Add" name="add_child"></td></tr>
    </table>
</form>
