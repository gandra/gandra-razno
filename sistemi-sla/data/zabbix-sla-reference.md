Zabbix sla docs: https://www.zabbix.com/documentation/7.0/en/manual/web_interface/frontend_sections/services/sla#overview

Zabbix sla report docs: https://www.zabbix.com/documentation/7.0/en/manual/web_interface/frontend_sections/services/sla_report

SLA main Page copy from browser:
```
SLA
Create SLA
Filter
Name
Status
AnyEnabledDisabled
Service tags
And/OrOr
tag
Contains
value
Remove
Add
ApplyReset
	
Name
SLO
Effective date
Reporting period	Timezone	Schedule	SLA report	
Status
	SQL Backup	100%	2025-10-17	Daily	System default: (UTC+00:00) UTC	24x7	SLA report	Enabled
	WIN-SERVER SLA	100%	2025-10-16	Daily	System default: (UTC+00:00) UTC	24x7	SLA report	Enabled
	WIN-WEEKLY	100%	2025-10-16	Weekly	System default: (UTC+00:00) UTC	24x7	SLA report	Enabled
Displaying 3 of 3 found
0 selectedEnableDisableDelete
```


SLA main Page outer html:
```
<div class="wrapper" style="overflow: auto;">
<script type="text/x-jquery-tmpl" id="filter-tag-row-tmpl">
	<tr class="form_row"><td><input type="text" name="filter_tags[#{rowNum}][tag]" value="" maxlength="255" placeholder="tag" style="width: 150px;"></td><td><z-select value="0" name="filter_tags[#{rowNum}][operator]" data-options="[{&quot;value&quot;:4,&quot;label&quot;:&quot;Exists&quot;},{&quot;value&quot;:1,&quot;label&quot;:&quot;Equals&quot;},{&quot;value&quot;:0,&quot;label&quot;:&quot;Contains&quot;},{&quot;value&quot;:5,&quot;label&quot;:&quot;Does not exist&quot;},{&quot;value&quot;:3,&quot;label&quot;:&quot;Does not equal&quot;},{&quot;value&quot;:2,&quot;label&quot;:&quot;Does not contain&quot;}]" tabindex="-1"></z-select></td><td><input type="text" name="filter_tags[#{rowNum}][value]" value="" maxlength="255" placeholder="value" style="width: 150px;"></td><td class="nowrap"><button type="button" id="filter_tags_#{rowNum}_remove" name="filter_tags[#{rowNum}][remove]" class="btn-link element-table-remove">Remove</button></td></tr></script>

<script>
	const view = new class {

		init() {
			this._initTagFilter();
			this._initActions();
		}

		_initTagFilter() {
			$('#filter-tags')
				.dynamicRows({template: '#filter-tag-row-tmpl'})
				.on('afteradd.dynamicRows', function () {
					const rows = this.querySelectorAll('.form_row');

					new CTagFilterItem(rows[rows.length - 1]);
				});

			document.querySelectorAll('#filter-tags .form_row').forEach((row) => {
				new CTagFilterItem(row);
			});
		}

		_initActions() {
			document.addEventListener('click', (e) => {
				if (e.target.classList.contains('js-create-sla')) {
					this._edit();
				}
				else if (e.target.classList.contains('js-edit-sla')) {
					this._edit({slaid: e.target.dataset.slaid});
				}
				else if (e.target.classList.contains('js-enable-sla')) {
					this._enable(e.target, [e.target.dataset.slaid]);
				}
				else if (e.target.classList.contains('js-disable-sla')) {
					this._disable(e.target, [e.target.dataset.slaid]);
				}
				else if (e.target.classList.contains('js-massenable-sla')) {
					this._enable(e.target, Object.keys(chkbxRange.getSelectedIds()));
				}
				else if (e.target.classList.contains('js-massdisable-sla')) {
					this._disable(e.target, Object.keys(chkbxRange.getSelectedIds()));
				}
				else if (e.target.classList.contains('js-massdelete-sla')) {
					this._delete(e.target, Object.keys(chkbxRange.getSelectedIds()));
				}
			});
		}

		_edit(parameters = {}) {
			const overlay = PopUp('popup.sla.edit', parameters, {
				dialogueid: 'sla_edit',
				dialogue_class: 'modal-popup-static',
				prevent_navigation: true
			});

			const dialogue = overlay.$dialogue[0];

			dialogue.addEventListener('dialogue.submit', (e) => this._reload(e.detail));
		}

		_reload(success) {
			postMessageOk(success.title);

			if ('messages' in success) {
				postMessageDetails('success', success.messages);
			}

			uncheckTableRows('sla');
			location.href = location.href;
		}

		_enable(target, slaids) {
			const confirmation = slaids.length > 1
				? "Enable selected SLAs?"				: "Enable selected SLA?";

			if (!window.confirm(confirmation)) {
				return;
			}

			const curl = new Curl('zabbix.php');
			curl.setArgument('action', 'sla.enable');

			this._post(target, slaids, curl);
		}

		_disable(target, slaids) {
			const confirmation = slaids.length > 1
				? "Disable selected SLAs?"				: "Disable selected SLA?";

			if (!window.confirm(confirmation)) {
				return;
			}

			const curl = new Curl('zabbix.php');
			curl.setArgument('action', 'sla.disable');

			this._post(target, slaids, curl);
		}

		_delete(target, slaids) {
			const confirmation = slaids.length > 1
				? "Delete selected SLAs?"				: "Delete selected SLA?";

			if (!window.confirm(confirmation)) {
				return;
			}

			const curl = new Curl('zabbix.php');
			curl.setArgument('action', 'sla.delete');

			this._post(target, slaids, curl);
		}

		_post(target, slaids, curl) {
			target.classList.add('is-loading');

			curl.setArgument(CSRF_TOKEN_NAME, "dae1472721fb0a909ec66b8b5f1b4e555152e0a16afa8018e31ab7745fbbe3ed");

			return fetch(curl.getUrl(), {
				method: 'POST',
				headers: {'Content-Type': 'application/json'},
				body: JSON.stringify({slaids})
			})
				.then((response) => response.json())
				.then((response) => {
					if ('error' in response) {
						if ('title' in response.error) {
							postMessageError(response.error.title);
						}

						postMessageDetails('error', response.error.messages);

						uncheckTableRows('sla', response.keepids ?? []);
					}
					else if ('success' in response) {
						postMessageOk(response.success.title);

						if ('messages' in response.success) {
							postMessageDetails('success', response.success.messages);
						}

						uncheckTableRows('sla');
					}

					location.href = location.href;
				})
				.catch(() => {
					clearMessages();

					const message_box = makeMessageBox('bad', ["Unexpected server error."]);

					addMessage(message_box);

					target.classList.remove('is-loading');
					target.blur();
				});
		}
	};
</script>
<header class="header-title"><nav class="sidebar-nav-toggle" role="navigation" aria-label="Sidebar control"><button type="button" class="btn-icon zi-menu" title="Show sidebar" id="sidebar-button-toggle"></button></nav><div><h1 id="page-title-general">SLA</h1></div><div class="header-doc-link"><a class="btn-icon zi-help" title="Help" target="_blank" rel="noopener noreferrer" href="https://www.zabbix.com/documentation/7.0/en/manual/web_interface/frontend_sections/services/sla#overview"></a></div><div class="header-controls"><nav aria-label="Content controls"><ul><li><button type="button" class="js-create-sla">Create SLA</button></li></ul></nav></div></header><main><div data-accessible="1" class="filter-space ui-tabs ui-corner-all ui-widget ui-widget-content ui-tabs-collapsible" id="filter_690d41ae4d132" data-profile-idx="web.sla.list.filter" data-profile-idx2="0" style="" aria-label="Filter"><ul class="filter-btn-container ui-tabs-nav ui-corner-all ui-helper-reset ui-helper-clearfix ui-widget-header" role="tablist"><li role="tab" tabindex="0" class="ui-tabs-tab ui-corner-top ui-state-default ui-tab ui-tabs-active ui-state-active" aria-controls="tab_0" aria-labelledby="ui-id-1" aria-selected="true" aria-expanded="true"><a class="btn zi-filter filter-trigger ui-tabs-anchor" href="#tab_0" tabindex="-1" id="ui-id-1">Filter</a></li></ul><form method="get" action="zabbix.php" accept-charset="utf-8" name="zbx_filter"><input type="hidden" id="action" name="action" value="sla.list"><div class="filter-container ui-tabs-panel ui-corner-bottom ui-widget-content" id="tab_0" aria-labelledby="ui-id-1" role="tabpanel" aria-hidden="false"><div class="table filter-forms"><div class="row"><div class="cell"><div class="form-grid label-width-true"><label for="filter_name">Name</label><div class="form-field"><input type="text" id="filter_name" name="filter_name" value="" maxlength="255" style="width: 300px;"></div><label>Status</label><div class="form-field"><ul id="filter_status" class="radio-list-control"><li><input type="radio" id="filter_status_0" name="filter_status" value="-1" checked="checked"><label for="filter_status_0">Any</label></li><li><input type="radio" id="filter_status_1" name="filter_status" value="1"><label for="filter_status_1">Enabled</label></li><li><input type="radio" id="filter_status_2" name="filter_status" value="0"><label for="filter_status_2">Disabled</label></li></ul></div></div></div><div class="cell"><div class="form-grid label-width-true"><label>Service tags</label><div class="form-field"><table id="filter-tags"><tbody><tr><td colspan="4"><ul id="filter_evaltype" class="radio-list-control"><li><input type="radio" id="filter_evaltype_0" name="filter_evaltype" value="0" checked="checked"><label for="filter_evaltype_0">And/Or</label></li><li><input type="radio" id="filter_evaltype_1" name="filter_evaltype" value="2"><label for="filter_evaltype_1">Or</label></li></ul></td></tr><tr class="form_row"><td><input type="text" id="filter_tags_0_tag" name="filter_tags[0][tag]" value="" maxlength="255" placeholder="tag" style="width: 150px;"></td><td><z-select value="0" id="filter_tags_0_operator" name="filter_tags[0][operator]" tabindex="-1" width="134" style="width: 134px;"><button type="button" class="focusable" id="filter_tags-0-operator-select">Contains</button><input name="filter_tags[0][operator]" type="hidden" value="0"><ul class="list"><li value="4" title="Exists">Exists</li><li value="1" title="Equals">Equals</li><li value="0" title="Contains">Contains</li><li value="5" title="Does not exist">Does not exist</li><li value="3" title="Does not equal">Does not equal</li><li value="2" title="Does not contain">Does not contain</li></ul></z-select></td><td><input type="text" id="filter_tags_0_value" name="filter_tags[0][value]" value="" maxlength="255" placeholder="value" style="width: 150px;"></td><td class="nowrap"><button type="button" name="filter_tags[0][remove]" class="btn-link element-table-remove">Remove</button></td></tr><tr><td colspan="3"><button type="button" name="tags_add" class="btn-link element-table-add">Add</button></td></tr></tbody></table></div></div></div></div></div><div class="filter-forms"><button type="submit" name="filter_set" value="1" onclick="javascript: chkbxRange.clearSelectedOnFilterChange();">Apply</button><button type="button" data-url="zabbix.php?action=sla.list&amp;filter_rst=1" class="btn-alt" onclick="javascript: chkbxRange.clearSelectedOnFilterChange();">Reset</button></div></div></form></div><script type="text/javascript">
jQuery("#filter_690d41ae4d132").tabs({"collapsible":true,"active":0}).show();jQuery("[autofocus=autofocus]", jQuery("#filter_690d41ae4d132")).filter(":visible").focus();jQuery("#filter_690d41ae4d132").on("tabsactivate", function(e, ui) {var active = ui.newPanel.length ? jQuery(this).tabs("option", "active") + 1 : 0;updateUserProfile("web.sla.list.filter.active", active, []);if (active) {jQuery("[autofocus=autofocus]", ui.newPanel).focus();}});
</script><form method="post" action="zabbix.php" accept-charset="utf-8" id="sla-list" name="sla_list"><table class="list-table" id="t690d41ae50faf150215974"><thead><tr><th class="cell-width"><input type="checkbox" id="all_slas" name="all_slas" value="1" class="checkbox-radio" onclick="checkAll('sla_list', 'all_slas', 'slaids');"><label for="all_slas"><span></span></label></th><th style="width: 15%;"><a href="zabbix.php?action=sla.list&amp;sort=name&amp;sortorder=DESC">Name<span class="arrow-up"></span></a></th><th><a href="zabbix.php?action=sla.list&amp;sort=slo&amp;sortorder=ASC">SLO</a></th><th><a href="zabbix.php?action=sla.list&amp;sort=effective_date&amp;sortorder=ASC">Effective date</a></th><th>Reporting period</th><th>Timezone</th><th>Schedule</th><th>SLA report</th><th><a href="zabbix.php?action=sla.list&amp;sort=status&amp;sortorder=ASC">Status</a></th></tr></thead><tbody><tr><td><input type="checkbox" id="slaids_6" name="slaids[6]" value="6" class="checkbox-radio"><label for="slaids_6"><span></span></label></td><td class="wordbreak"><a class="js-edit-sla" data-slaid="6" role="button" href="javascript:void(0)">SQL Backup</a></td><td><span>100%</span></td><td>2025-10-17</td><td>Daily</td><td>System default: (UTC+00:00) UTC</td><td><span>24x7</span></td><td><a href="zabbix.php?action=slareport.list&amp;filter_slaid=6&amp;filter_set=1">SLA report</a></td><td><a class="link-action green js-disable-sla" data-slaid="6" role="button" href="javascript:void(0)">Enabled</a></td></tr><tr><td><input type="checkbox" id="slaids_3" name="slaids[3]" value="3" class="checkbox-radio"><label for="slaids_3"><span></span></label></td><td class="wordbreak"><a class="js-edit-sla" data-slaid="3" role="button" href="javascript:void(0)">WIN-SERVER SLA</a></td><td><span>100%</span></td><td>2025-10-16</td><td>Daily</td><td>System default: (UTC+00:00) UTC</td><td><span>24x7</span></td><td><a href="zabbix.php?action=slareport.list&amp;filter_slaid=3&amp;filter_set=1">SLA report</a></td><td><a class="link-action green js-disable-sla" data-slaid="3" role="button" href="javascript:void(0)">Enabled</a></td></tr><tr><td><input type="checkbox" id="slaids_4" name="slaids[4]" value="4" class="checkbox-radio"><label for="slaids_4"><span></span></label></td><td class="wordbreak"><a class="js-edit-sla" data-slaid="4" role="button" href="javascript:void(0)">WIN-WEEKLY</a></td><td><span>100%</span></td><td>2025-10-16</td><td>Weekly</td><td>System default: (UTC+00:00) UTC</td><td><span>24x7</span></td><td><a href="zabbix.php?action=slareport.list&amp;filter_slaid=4&amp;filter_set=1">SLA report</a></td><td><a class="link-action green js-disable-sla" data-slaid="4" role="button" href="javascript:void(0)">Enabled</a></td></tr></tbody></table><div class="table-paging"><nav class="paging-btn-container" role="navigation" aria-label="Pager"><div class="table-stats">Displaying 3 of 3 found</div></nav></div><div id="action_buttons" class="action-buttons"><span id="selected_count" class="selected-item-count">0 selected</span><button type="button" class="btn-alt js-massenable-sla js-no-chkbxrange" disabled="">Enable</button><button type="button" class="btn-alt js-massdisable-sla js-no-chkbxrange" disabled="">Disable</button><button type="button" class="btn-alt js-massdelete-sla js-no-chkbxrange" disabled="">Delete</button></div></form><div hidden="" class="overlay-dialogue notif ui-draggable" style="display: none; right: 10px; top: 10px;"><div class="overlay-dialogue-header cursor-move ui-draggable-handle"><ul><li><button title="Snooze for Admin" class="btn-icon zi-bell"></button></li><li><button title="Mute for Admin" class="btn-icon zi-speaker"></button></li></ul><button title="Close" type="button" class="btn-overlay-close"></button></div><ul class="notif-body"></ul></div></main><script>jQuery(function($){
	view.init();
});</script><output id="msg-global-footer" class="msg-global-footer msg-warning" style="left: 185px; width: 1253px;"></output><footer role="contentinfo">Zabbix 7.0.12. © 2001–2025, <a class="grey link-alt" target="_blank" rel="noopener noreferrer" href="https://www.zabbix.com/">Zabbix SIA</a></footer>
<script type="text/javascript">
	$(function() {
		
		// the chkbxRange.init() method must be called after the inserted post scripts and initializing cookies
		cookie.init();
		chkbxRange.init();
	});

	/**
	 * Toggles filter state and updates title and icons accordingly.
	 *
	 * @param {string} 	idx					User profile index
	 * @param {string} 	value				Value
	 * @param {object} 	idx2				An array of IDs
	 * @param {int} 	profile_type		Profile type
	 */
	function updateUserProfile(idx, value, idx2, profile_type = PROFILE_TYPE_INT) {
		const value_fields = {
			[PROFILE_TYPE_INT]: 'value_int',
			[PROFILE_TYPE_STR]: 'value_str'
		};

		return sendAjaxData('zabbix.php?action=profile.update', {
			data: {
				idx: idx,
				[value_fields[profile_type]]: value,
				idx2: idx2,
				[CSRF_TOKEN_NAME]: "305140a7a37d610be17b7d3d7f3babd66823af784e2b6b20f2a03165997fcc55"			}
		});
	}

	/**
	 * Add object to the list of favorites.
	 */
	function add2favorites(object, objectid) {
		sendAjaxData('zabbix.php?action=favorite.create', {
			data: {
				object: object,
				objectid: objectid,
				[CSRF_TOKEN_NAME]: "902bfeb4a5498b0aaf54236c4eb5df617965a90a7d60e963704c19cd3375de15"			}
		});
	}

	/**
	 * Remove object from the list of favorites. Remove all favorites if objectid==0.
	 */
	function rm4favorites(object, objectid) {
		sendAjaxData('zabbix.php?action=favorite.delete', {
			data: {
				object: object,
				objectid: objectid,
				[CSRF_TOKEN_NAME]: "902bfeb4a5498b0aaf54236c4eb5df617965a90a7d60e963704c19cd3375de15"			}
		});
	}
</script>
<script type="text/javascript">
chkbxRange.pageGoName = "slaids";
chkbxRange.prefix = "sla";
</script></div>
```


SLA CREATE Page copy from browser:
```
New SLA

SLAExcluded downtimes
Name
SLO
99.9
 %
Reporting period
DailyWeeklyMonthlyQuarterlyAnnually
Time zone
System default: (UTC+00:00) UTC
Schedule
24x7Custom
Effective date
2025-11-07

Service tags
Name	Operation	Value	Action
tag
Equals
value
Remove
Add
Description
Enabled

AddCance
```

SLA CREATE Page outer html:
```
<div class="overlay-dialogue modal modal-popup modal-popup-static" data-dialogueid="sla_edit" role="dialog" aria-modal="true" aria-labelledby="overlay-dialogue-header-title-sla_edit" data-prevent-navigation="true" style="left: 353px;"><div class="overlay-dialogue-header"><h4 id="overlay-dialogue-header-title-sla_edit">New SLA</h4>
					<a class="btn-icon zi-help-small" target="_blank" title="Help" href="https://www.zabbix.com/documentation/7.0/en/manual/it_services/sla#configuration"></a>
				<button class="btn-overlay-close" title="Close"></button></div><div class="overlay-dialogue-body" style="overflow-y: hidden;"><form method="post" action="zabbix.php" accept-charset="utf-8" id="sla-form" name="sla_form" style=""><input type="hidden" name="_csrf_token" value="dae1472721fb0a909ec66b8b5f1b4e555152e0a16afa8018e31ab7745fbbe3ed"><button type="submit" class="form-submit-hidden"></button><div id="tabs" class="table-forms-container ui-tabs ui-corner-all ui-widget ui-widget-content"><ul class="ui-tabs-nav tabs-nav ui-corner-all ui-helper-reset ui-helper-clearfix ui-widget-header" role="tablist"><li role="tab" tabindex="0" class="ui-tabs-tab ui-corner-top ui-state-default ui-tab ui-tabs-active ui-state-active" aria-controls="sla-tab" aria-labelledby="tab_sla-tab" aria-selected="true" aria-expanded="true"><a id="tab_sla-tab" href="#sla-tab" tabindex="-1" class="ui-tabs-anchor">SLA</a></li><li role="tab" tabindex="-1" class="ui-tabs-tab ui-corner-top ui-state-default ui-tab" aria-controls="excluded-downtimes-tab" aria-labelledby="tab_excluded-downtimes-tab" aria-selected="false" aria-expanded="false"><a id="tab_excluded-downtimes-tab" js-indicator="excluded-downtimes" href="#excluded-downtimes-tab" tabindex="-1" class="ui-tabs-anchor" data-indicator="count" data-indicator-value="0">Excluded downtimes</a></li></ul><div id="sla-tab" aria-hidden="false" aria-labelledby="tab_sla-tab" role="tabpanel" class="ui-tabs-panel ui-corner-bottom ui-widget-content"><div class="form-grid" style="--label-width: 100px;"><label for="name" class="form-label-asterisk">Name</label><div class="form-field"><input type="text" id="name" name="name" value="" maxlength="255" style="width: 453px;" aria-required="true" autofocus="autofocus"></div><label for="slo" class="form-label-asterisk">SLO</label><div class="form-field"><input type="text" id="slo" name="slo" value="" maxlength="7" style="width: 75px;" placeholder="99.9" aria-required="true"> %</div><label>Reporting period</label><div class="form-field"><ul id="period" class="radio-list-control"><li><input type="radio" id="period_0" name="period" value="0"><label for="period_0">Daily</label></li><li><input type="radio" id="period_1" name="period" value="1" checked="checked"><label for="period_1">Weekly</label></li><li><input type="radio" id="period_2" name="period" value="2"><label for="period_2">Monthly</label></li><li><input type="radio" id="period_3" name="period" value="3"><label for="period_3">Quarterly</label></li><li><input type="radio" id="period_4" name="period" value="4"><label for="period_4">Annually</label></li></ul></div><label for="timezone-focusable">Time zone</label><div class="form-field"><z-select id="timezone" value="system" name="timezone" tabindex="-1" width="303" style="width: 303px;"><button type="button" class="focusable" id="timezone-focusable">System default: (UTC+00:00) UTC</button><input name="timezone" type="hidden" value="system"><ul class="list"><li value="system" title="System default: (UTC+00:00) UTC">System default: (UTC+00:00) UTC</li><li value="Atlantic/Azores" title="(UTC-01:00) Atlantic/Azores">(UTC-01:00) Atlantic/Azores</li><li value="Atlantic/Cape_Verde" title="(UTC-01:00) Atlantic/Cape_Verde">(UTC-01:00) Atlantic/Cape_Verde</li><li value="America/Noronha" title="(UTC-02:00) America/Noronha">(UTC-02:00) America/Noronha</li><li value="America/Nuuk" title="(UTC-02:00) America/Nuuk">(UTC-02:00) America/Nuuk</li><li value="America/Scoresbysund" title="(UTC-02:00) America/Scoresbysund">(UTC-02:00) America/Scoresbysund</li><li value="Atlantic/South_Georgia" title="(UTC-02:00) Atlantic/South_Georgia">(UTC-02:00) Atlantic/South_Georgia</li><li value="America/Araguaina" title="(UTC-03:00) America/Araguaina">(UTC-03:00) America/Araguaina</li><li value="America/Argentina/Buenos_Aires" title="(UTC-03:00) America/Argentina/Buenos_Aires">(UTC-03:00) America/Argentina/Buenos_Aires</li><li value="America/Argentina/Catamarca" title="(UTC-03:00) America/Argentina/Catamarca">(UTC-03:00) America/Argentina/Catamarca</li><li value="America/Argentina/Cordoba" title="(UTC-03:00) America/Argentina/Cordoba">(UTC-03:00) America/Argentina/Cordoba</li><li value="America/Argentina/Jujuy" title="(UTC-03:00) America/Argentina/Jujuy">(UTC-03:00) America/Argentina/Jujuy</li><li value="America/Argentina/La_Rioja" title="(UTC-03:00) America/Argentina/La_Rioja">(UTC-03:00) America/Argentina/La_Rioja</li><li value="America/Argentina/Mendoza" title="(UTC-03:00) America/Argentina/Mendoza">(UTC-03:00) America/Argentina/Mendoza</li><li value="America/Argentina/Rio_Gallegos" title="(UTC-03:00) America/Argentina/Rio_Gallegos">(UTC-03:00) America/Argentina/Rio_Gallegos</li><li value="America/Argentina/Salta" title="(UTC-03:00) America/Argentina/Salta">(UTC-03:00) America/Argentina/Salta</li><li value="America/Argentina/San_Juan" title="(UTC-03:00) America/Argentina/San_Juan">(UTC-03:00) America/Argentina/San_Juan</li><li value="America/Argentina/San_Luis" title="(UTC-03:00) America/Argentina/San_Luis">(UTC-03:00) America/Argentina/San_Luis</li><li value="America/Argentina/Tucuman" title="(UTC-03:00) America/Argentina/Tucuman">(UTC-03:00) America/Argentina/Tucuman</li><li value="America/Argentina/Ushuaia" title="(UTC-03:00) America/Argentina/Ushuaia">(UTC-03:00) America/Argentina/Ushuaia</li><li value="America/Asuncion" title="(UTC-03:00) America/Asuncion">(UTC-03:00) America/Asuncion</li><li value="America/Bahia" title="(UTC-03:00) America/Bahia">(UTC-03:00) America/Bahia</li><li value="America/Belem" title="(UTC-03:00) America/Belem">(UTC-03:00) America/Belem</li><li value="America/Cayenne" title="(UTC-03:00) America/Cayenne">(UTC-03:00) America/Cayenne</li><li value="America/Coyhaique" title="(UTC-03:00) America/Coyhaique">(UTC-03:00) America/Coyhaique</li><li value="America/Fortaleza" title="(UTC-03:00) America/Fortaleza">(UTC-03:00) America/Fortaleza</li><li value="America/Maceio" title="(UTC-03:00) America/Maceio">(UTC-03:00) America/Maceio</li><li value="America/Miquelon" title="(UTC-03:00) America/Miquelon">(UTC-03:00) America/Miquelon</li><li value="America/Montevideo" title="(UTC-03:00) America/Montevideo">(UTC-03:00) America/Montevideo</li><li value="America/Paramaribo" title="(UTC-03:00) America/Paramaribo">(UTC-03:00) America/Paramaribo</li><li value="America/Punta_Arenas" title="(UTC-03:00) America/Punta_Arenas">(UTC-03:00) America/Punta_Arenas</li><li value="America/Recife" title="(UTC-03:00) America/Recife">(UTC-03:00) America/Recife</li><li value="America/Santarem" title="(UTC-03:00) America/Santarem">(UTC-03:00) America/Santarem</li><li value="America/Santiago" title="(UTC-03:00) America/Santiago">(UTC-03:00) America/Santiago</li><li value="America/Sao_Paulo" title="(UTC-03:00) America/Sao_Paulo">(UTC-03:00) America/Sao_Paulo</li><li value="Antarctica/Palmer" title="(UTC-03:00) Antarctica/Palmer">(UTC-03:00) Antarctica/Palmer</li><li value="Antarctica/Rothera" title="(UTC-03:00) Antarctica/Rothera">(UTC-03:00) Antarctica/Rothera</li><li value="Atlantic/Stanley" title="(UTC-03:00) Atlantic/Stanley">(UTC-03:00) Atlantic/Stanley</li><li value="America/St_Johns" title="(UTC-03:30) America/St_Johns">(UTC-03:30) America/St_Johns</li><li value="America/Anguilla" title="(UTC-04:00) America/Anguilla">(UTC-04:00) America/Anguilla</li><li value="America/Antigua" title="(UTC-04:00) America/Antigua">(UTC-04:00) America/Antigua</li><li value="America/Aruba" title="(UTC-04:00) America/Aruba">(UTC-04:00) America/Aruba</li><li value="America/Barbados" title="(UTC-04:00) America/Barbados">(UTC-04:00) America/Barbados</li><li value="America/Blanc-Sablon" title="(UTC-04:00) America/Blanc-Sablon">(UTC-04:00) America/Blanc-Sablon</li><li value="America/Boa_Vista" title="(UTC-04:00) America/Boa_Vista">(UTC-04:00) America/Boa_Vista</li><li value="America/Campo_Grande" title="(UTC-04:00) America/Campo_Grande">(UTC-04:00) America/Campo_Grande</li><li value="America/Caracas" title="(UTC-04:00) America/Caracas">(UTC-04:00) America/Caracas</li><li value="America/Cuiaba" title="(UTC-04:00) America/Cuiaba">(UTC-04:00) America/Cuiaba</li><li value="America/Curacao" title="(UTC-04:00) America/Curacao">(UTC-04:00) America/Curacao</li><li value="America/Dominica" title="(UTC-04:00) America/Dominica">(UTC-04:00) America/Dominica</li><li value="America/Glace_Bay" title="(UTC-04:00) America/Glace_Bay">(UTC-04:00) America/Glace_Bay</li><li value="America/Goose_Bay" title="(UTC-04:00) America/Goose_Bay">(UTC-04:00) America/Goose_Bay</li><li value="America/Grenada" title="(UTC-04:00) America/Grenada">(UTC-04:00) America/Grenada</li><li value="America/Guadeloupe" title="(UTC-04:00) America/Guadeloupe">(UTC-04:00) America/Guadeloupe</li><li value="America/Guyana" title="(UTC-04:00) America/Guyana">(UTC-04:00) America/Guyana</li><li value="America/Halifax" title="(UTC-04:00) America/Halifax">(UTC-04:00) America/Halifax</li><li value="America/Kralendijk" title="(UTC-04:00) America/Kralendijk">(UTC-04:00) America/Kralendijk</li><li value="America/La_Paz" title="(UTC-04:00) America/La_Paz">(UTC-04:00) America/La_Paz</li><li value="America/Lower_Princes" title="(UTC-04:00) America/Lower_Princes">(UTC-04:00) America/Lower_Princes</li><li value="America/Manaus" title="(UTC-04:00) America/Manaus">(UTC-04:00) America/Manaus</li><li value="America/Marigot" title="(UTC-04:00) America/Marigot">(UTC-04:00) America/Marigot</li><li value="America/Martinique" title="(UTC-04:00) America/Martinique">(UTC-04:00) America/Martinique</li><li value="America/Moncton" title="(UTC-04:00) America/Moncton">(UTC-04:00) America/Moncton</li><li value="America/Montserrat" title="(UTC-04:00) America/Montserrat">(UTC-04:00) America/Montserrat</li><li value="America/Porto_Velho" title="(UTC-04:00) America/Porto_Velho">(UTC-04:00) America/Porto_Velho</li><li value="America/Port_of_Spain" title="(UTC-04:00) America/Port_of_Spain">(UTC-04:00) America/Port_of_Spain</li><li value="America/Puerto_Rico" title="(UTC-04:00) America/Puerto_Rico">(UTC-04:00) America/Puerto_Rico</li><li value="America/Santo_Domingo" title="(UTC-04:00) America/Santo_Domingo">(UTC-04:00) America/Santo_Domingo</li><li value="America/St_Barthelemy" title="(UTC-04:00) America/St_Barthelemy">(UTC-04:00) America/St_Barthelemy</li><li value="America/St_Kitts" title="(UTC-04:00) America/St_Kitts">(UTC-04:00) America/St_Kitts</li><li value="America/St_Lucia" title="(UTC-04:00) America/St_Lucia">(UTC-04:00) America/St_Lucia</li><li value="America/St_Thomas" title="(UTC-04:00) America/St_Thomas">(UTC-04:00) America/St_Thomas</li><li value="America/St_Vincent" title="(UTC-04:00) America/St_Vincent">(UTC-04:00) America/St_Vincent</li><li value="America/Thule" title="(UTC-04:00) America/Thule">(UTC-04:00) America/Thule</li><li value="America/Tortola" title="(UTC-04:00) America/Tortola">(UTC-04:00) America/Tortola</li><li value="Atlantic/Bermuda" title="(UTC-04:00) Atlantic/Bermuda">(UTC-04:00) Atlantic/Bermuda</li><li value="America/Atikokan" title="(UTC-05:00) America/Atikokan">(UTC-05:00) America/Atikokan</li><li value="America/Bogota" title="(UTC-05:00) America/Bogota">(UTC-05:00) America/Bogota</li><li value="America/Cancun" title="(UTC-05:00) America/Cancun">(UTC-05:00) America/Cancun</li><li value="America/Cayman" title="(UTC-05:00) America/Cayman">(UTC-05:00) America/Cayman</li><li value="America/Detroit" title="(UTC-05:00) America/Detroit">(UTC-05:00) America/Detroit</li><li value="America/Eirunepe" title="(UTC-05:00) America/Eirunepe">(UTC-05:00) America/Eirunepe</li><li value="America/Grand_Turk" title="(UTC-05:00) America/Grand_Turk">(UTC-05:00) America/Grand_Turk</li><li value="America/Guayaquil" title="(UTC-05:00) America/Guayaquil">(UTC-05:00) America/Guayaquil</li><li value="America/Havana" title="(UTC-05:00) America/Havana">(UTC-05:00) America/Havana</li><li value="America/Indiana/Indianapolis" title="(UTC-05:00) America/Indiana/Indianapolis">(UTC-05:00) America/Indiana/Indianapolis</li><li value="America/Indiana/Marengo" title="(UTC-05:00) America/Indiana/Marengo">(UTC-05:00) America/Indiana/Marengo</li><li value="America/Indiana/Petersburg" title="(UTC-05:00) America/Indiana/Petersburg">(UTC-05:00) America/Indiana/Petersburg</li><li value="America/Indiana/Vevay" title="(UTC-05:00) America/Indiana/Vevay">(UTC-05:00) America/Indiana/Vevay</li><li value="America/Indiana/Vincennes" title="(UTC-05:00) America/Indiana/Vincennes">(UTC-05:00) America/Indiana/Vincennes</li><li value="America/Indiana/Winamac" title="(UTC-05:00) America/Indiana/Winamac">(UTC-05:00) America/Indiana/Winamac</li><li value="America/Iqaluit" title="(UTC-05:00) America/Iqaluit">(UTC-05:00) America/Iqaluit</li><li value="America/Jamaica" title="(UTC-05:00) America/Jamaica">(UTC-05:00) America/Jamaica</li><li value="America/Kentucky/Louisville" title="(UTC-05:00) America/Kentucky/Louisville">(UTC-05:00) America/Kentucky/Louisville</li><li value="America/Kentucky/Monticello" title="(UTC-05:00) America/Kentucky/Monticello">(UTC-05:00) America/Kentucky/Monticello</li><li value="America/Lima" title="(UTC-05:00) America/Lima">(UTC-05:00) America/Lima</li><li value="America/Nassau" title="(UTC-05:00) America/Nassau">(UTC-05:00) America/Nassau</li><li value="America/New_York" title="(UTC-05:00) America/New_York">(UTC-05:00) America/New_York</li><li value="America/Panama" title="(UTC-05:00) America/Panama">(UTC-05:00) America/Panama</li><li value="America/Port-au-Prince" title="(UTC-05:00) America/Port-au-Prince">(UTC-05:00) America/Port-au-Prince</li><li value="America/Rio_Branco" title="(UTC-05:00) America/Rio_Branco">(UTC-05:00) America/Rio_Branco</li><li value="America/Toronto" title="(UTC-05:00) America/Toronto">(UTC-05:00) America/Toronto</li><li value="Pacific/Easter" title="(UTC-05:00) Pacific/Easter">(UTC-05:00) Pacific/Easter</li><li value="America/Bahia_Banderas" title="(UTC-06:00) America/Bahia_Banderas">(UTC-06:00) America/Bahia_Banderas</li><li value="America/Belize" title="(UTC-06:00) America/Belize">(UTC-06:00) America/Belize</li><li value="America/Chicago" title="(UTC-06:00) America/Chicago">(UTC-06:00) America/Chicago</li><li value="America/Chihuahua" title="(UTC-06:00) America/Chihuahua">(UTC-06:00) America/Chihuahua</li><li value="America/Costa_Rica" title="(UTC-06:00) America/Costa_Rica">(UTC-06:00) America/Costa_Rica</li><li value="America/El_Salvador" title="(UTC-06:00) America/El_Salvador">(UTC-06:00) America/El_Salvador</li><li value="America/Guatemala" title="(UTC-06:00) America/Guatemala">(UTC-06:00) America/Guatemala</li><li value="America/Indiana/Knox" title="(UTC-06:00) America/Indiana/Knox">(UTC-06:00) America/Indiana/Knox</li><li value="America/Indiana/Tell_City" title="(UTC-06:00) America/Indiana/Tell_City">(UTC-06:00) America/Indiana/Tell_City</li><li value="America/Managua" title="(UTC-06:00) America/Managua">(UTC-06:00) America/Managua</li><li value="America/Matamoros" title="(UTC-06:00) America/Matamoros">(UTC-06:00) America/Matamoros</li><li value="America/Menominee" title="(UTC-06:00) America/Menominee">(UTC-06:00) America/Menominee</li><li value="America/Merida" title="(UTC-06:00) America/Merida">(UTC-06:00) America/Merida</li><li value="America/Mexico_City" title="(UTC-06:00) America/Mexico_City">(UTC-06:00) America/Mexico_City</li><li value="America/Monterrey" title="(UTC-06:00) America/Monterrey">(UTC-06:00) America/Monterrey</li><li value="America/North_Dakota/Beulah" title="(UTC-06:00) America/North_Dakota/Beulah">(UTC-06:00) America/North_Dakota/Beulah</li><li value="America/North_Dakota/Center" title="(UTC-06:00) America/North_Dakota/Center">(UTC-06:00) America/North_Dakota/Center</li><li value="America/North_Dakota/New_Salem" title="(UTC-06:00) America/North_Dakota/New_Salem">(UTC-06:00) America/North_Dakota/New_Salem</li><li value="America/Ojinaga" title="(UTC-06:00) America/Ojinaga">(UTC-06:00) America/Ojinaga</li><li value="America/Rankin_Inlet" title="(UTC-06:00) America/Rankin_Inlet">(UTC-06:00) America/Rankin_Inlet</li><li value="America/Regina" title="(UTC-06:00) America/Regina">(UTC-06:00) America/Regina</li><li value="America/Resolute" title="(UTC-06:00) America/Resolute">(UTC-06:00) America/Resolute</li><li value="America/Swift_Current" title="(UTC-06:00) America/Swift_Current">(UTC-06:00) America/Swift_Current</li><li value="America/Tegucigalpa" title="(UTC-06:00) America/Tegucigalpa">(UTC-06:00) America/Tegucigalpa</li><li value="America/Winnipeg" title="(UTC-06:00) America/Winnipeg">(UTC-06:00) America/Winnipeg</li><li value="Pacific/Galapagos" title="(UTC-06:00) Pacific/Galapagos">(UTC-06:00) Pacific/Galapagos</li><li value="America/Boise" title="(UTC-07:00) America/Boise">(UTC-07:00) America/Boise</li><li value="America/Cambridge_Bay" title="(UTC-07:00) America/Cambridge_Bay">(UTC-07:00) America/Cambridge_Bay</li><li value="America/Ciudad_Juarez" title="(UTC-07:00) America/Ciudad_Juarez">(UTC-07:00) America/Ciudad_Juarez</li><li value="America/Creston" title="(UTC-07:00) America/Creston">(UTC-07:00) America/Creston</li><li value="America/Dawson" title="(UTC-07:00) America/Dawson">(UTC-07:00) America/Dawson</li><li value="America/Dawson_Creek" title="(UTC-07:00) America/Dawson_Creek">(UTC-07:00) America/Dawson_Creek</li><li value="America/Denver" title="(UTC-07:00) America/Denver">(UTC-07:00) America/Denver</li><li value="America/Edmonton" title="(UTC-07:00) America/Edmonton">(UTC-07:00) America/Edmonton</li><li value="America/Fort_Nelson" title="(UTC-07:00) America/Fort_Nelson">(UTC-07:00) America/Fort_Nelson</li><li value="America/Hermosillo" title="(UTC-07:00) America/Hermosillo">(UTC-07:00) America/Hermosillo</li><li value="America/Inuvik" title="(UTC-07:00) America/Inuvik">(UTC-07:00) America/Inuvik</li><li value="America/Mazatlan" title="(UTC-07:00) America/Mazatlan">(UTC-07:00) America/Mazatlan</li><li value="America/Phoenix" title="(UTC-07:00) America/Phoenix">(UTC-07:00) America/Phoenix</li><li value="America/Whitehorse" title="(UTC-07:00) America/Whitehorse">(UTC-07:00) America/Whitehorse</li><li value="America/Los_Angeles" title="(UTC-08:00) America/Los_Angeles">(UTC-08:00) America/Los_Angeles</li><li value="America/Tijuana" title="(UTC-08:00) America/Tijuana">(UTC-08:00) America/Tijuana</li><li value="America/Vancouver" title="(UTC-08:00) America/Vancouver">(UTC-08:00) America/Vancouver</li><li value="Pacific/Pitcairn" title="(UTC-08:00) Pacific/Pitcairn">(UTC-08:00) Pacific/Pitcairn</li><li value="America/Anchorage" title="(UTC-09:00) America/Anchorage">(UTC-09:00) America/Anchorage</li><li value="America/Juneau" title="(UTC-09:00) America/Juneau">(UTC-09:00) America/Juneau</li><li value="America/Metlakatla" title="(UTC-09:00) America/Metlakatla">(UTC-09:00) America/Metlakatla</li><li value="America/Nome" title="(UTC-09:00) America/Nome">(UTC-09:00) America/Nome</li><li value="America/Sitka" title="(UTC-09:00) America/Sitka">(UTC-09:00) America/Sitka</li><li value="America/Yakutat" title="(UTC-09:00) America/Yakutat">(UTC-09:00) America/Yakutat</li><li value="Pacific/Gambier" title="(UTC-09:00) Pacific/Gambier">(UTC-09:00) Pacific/Gambier</li><li value="Pacific/Marquesas" title="(UTC-09:30) Pacific/Marquesas">(UTC-09:30) Pacific/Marquesas</li><li value="America/Adak" title="(UTC-10:00) America/Adak">(UTC-10:00) America/Adak</li><li value="Pacific/Honolulu" title="(UTC-10:00) Pacific/Honolulu">(UTC-10:00) Pacific/Honolulu</li><li value="Pacific/Rarotonga" title="(UTC-10:00) Pacific/Rarotonga">(UTC-10:00) Pacific/Rarotonga</li><li value="Pacific/Tahiti" title="(UTC-10:00) Pacific/Tahiti">(UTC-10:00) Pacific/Tahiti</li><li value="Pacific/Midway" title="(UTC-11:00) Pacific/Midway">(UTC-11:00) Pacific/Midway</li><li value="Pacific/Niue" title="(UTC-11:00) Pacific/Niue">(UTC-11:00) Pacific/Niue</li><li value="Pacific/Pago_Pago" title="(UTC-11:00) Pacific/Pago_Pago">(UTC-11:00) Pacific/Pago_Pago</li><li value="Africa/Abidjan" title="(UTC+00:00) Africa/Abidjan">(UTC+00:00) Africa/Abidjan</li><li value="Africa/Accra" title="(UTC+00:00) Africa/Accra">(UTC+00:00) Africa/Accra</li><li value="Africa/Bamako" title="(UTC+00:00) Africa/Bamako">(UTC+00:00) Africa/Bamako</li><li value="Africa/Banjul" title="(UTC+00:00) Africa/Banjul">(UTC+00:00) Africa/Banjul</li><li value="Africa/Bissau" title="(UTC+00:00) Africa/Bissau">(UTC+00:00) Africa/Bissau</li><li value="Africa/Conakry" title="(UTC+00:00) Africa/Conakry">(UTC+00:00) Africa/Conakry</li><li value="Africa/Dakar" title="(UTC+00:00) Africa/Dakar">(UTC+00:00) Africa/Dakar</li><li value="Africa/Freetown" title="(UTC+00:00) Africa/Freetown">(UTC+00:00) Africa/Freetown</li><li value="Africa/Lome" title="(UTC+00:00) Africa/Lome">(UTC+00:00) Africa/Lome</li><li value="Africa/Monrovia" title="(UTC+00:00) Africa/Monrovia">(UTC+00:00) Africa/Monrovia</li><li value="Africa/Nouakchott" title="(UTC+00:00) Africa/Nouakchott">(UTC+00:00) Africa/Nouakchott</li><li value="Africa/Ouagadougou" title="(UTC+00:00) Africa/Ouagadougou">(UTC+00:00) Africa/Ouagadougou</li><li value="Africa/Sao_Tome" title="(UTC+00:00) Africa/Sao_Tome">(UTC+00:00) Africa/Sao_Tome</li><li value="America/Danmarkshavn" title="(UTC+00:00) America/Danmarkshavn">(UTC+00:00) America/Danmarkshavn</li><li value="Antarctica/Troll" title="(UTC+00:00) Antarctica/Troll">(UTC+00:00) Antarctica/Troll</li><li value="Atlantic/Canary" title="(UTC+00:00) Atlantic/Canary">(UTC+00:00) Atlantic/Canary</li><li value="Atlantic/Faroe" title="(UTC+00:00) Atlantic/Faroe">(UTC+00:00) Atlantic/Faroe</li><li value="Atlantic/Madeira" title="(UTC+00:00) Atlantic/Madeira">(UTC+00:00) Atlantic/Madeira</li><li value="Atlantic/Reykjavik" title="(UTC+00:00) Atlantic/Reykjavik">(UTC+00:00) Atlantic/Reykjavik</li><li value="Atlantic/St_Helena" title="(UTC+00:00) Atlantic/St_Helena">(UTC+00:00) Atlantic/St_Helena</li><li value="Europe/Dublin" title="(UTC+00:00) Europe/Dublin">(UTC+00:00) Europe/Dublin</li><li value="Europe/Guernsey" title="(UTC+00:00) Europe/Guernsey">(UTC+00:00) Europe/Guernsey</li><li value="Europe/Isle_of_Man" title="(UTC+00:00) Europe/Isle_of_Man">(UTC+00:00) Europe/Isle_of_Man</li><li value="Europe/Jersey" title="(UTC+00:00) Europe/Jersey">(UTC+00:00) Europe/Jersey</li><li value="Europe/Lisbon" title="(UTC+00:00) Europe/Lisbon">(UTC+00:00) Europe/Lisbon</li><li value="Europe/London" title="(UTC+00:00) Europe/London">(UTC+00:00) Europe/London</li><li value="UTC" title="(UTC+00:00) UTC">(UTC+00:00) UTC</li><li value="Africa/Algiers" title="(UTC+01:00) Africa/Algiers">(UTC+01:00) Africa/Algiers</li><li value="Africa/Bangui" title="(UTC+01:00) Africa/Bangui">(UTC+01:00) Africa/Bangui</li><li value="Africa/Brazzaville" title="(UTC+01:00) Africa/Brazzaville">(UTC+01:00) Africa/Brazzaville</li><li value="Africa/Casablanca" title="(UTC+01:00) Africa/Casablanca">(UTC+01:00) Africa/Casablanca</li><li value="Africa/Ceuta" title="(UTC+01:00) Africa/Ceuta">(UTC+01:00) Africa/Ceuta</li><li value="Africa/Douala" title="(UTC+01:00) Africa/Douala">(UTC+01:00) Africa/Douala</li><li value="Africa/El_Aaiun" title="(UTC+01:00) Africa/El_Aaiun">(UTC+01:00) Africa/El_Aaiun</li><li value="Africa/Kinshasa" title="(UTC+01:00) Africa/Kinshasa">(UTC+01:00) Africa/Kinshasa</li><li value="Africa/Lagos" title="(UTC+01:00) Africa/Lagos">(UTC+01:00) Africa/Lagos</li><li value="Africa/Libreville" title="(UTC+01:00) Africa/Libreville">(UTC+01:00) Africa/Libreville</li><li value="Africa/Luanda" title="(UTC+01:00) Africa/Luanda">(UTC+01:00) Africa/Luanda</li><li value="Africa/Malabo" title="(UTC+01:00) Africa/Malabo">(UTC+01:00) Africa/Malabo</li><li value="Africa/Ndjamena" title="(UTC+01:00) Africa/Ndjamena">(UTC+01:00) Africa/Ndjamena</li><li value="Africa/Niamey" title="(UTC+01:00) Africa/Niamey">(UTC+01:00) Africa/Niamey</li><li value="Africa/Porto-Novo" title="(UTC+01:00) Africa/Porto-Novo">(UTC+01:00) Africa/Porto-Novo</li><li value="Africa/Tunis" title="(UTC+01:00) Africa/Tunis">(UTC+01:00) Africa/Tunis</li><li value="Arctic/Longyearbyen" title="(UTC+01:00) Arctic/Longyearbyen">(UTC+01:00) Arctic/Longyearbyen</li><li value="Europe/Amsterdam" title="(UTC+01:00) Europe/Amsterdam">(UTC+01:00) Europe/Amsterdam</li><li value="Europe/Andorra" title="(UTC+01:00) Europe/Andorra">(UTC+01:00) Europe/Andorra</li><li value="Europe/Belgrade" title="(UTC+01:00) Europe/Belgrade">(UTC+01:00) Europe/Belgrade</li><li value="Europe/Berlin" title="(UTC+01:00) Europe/Berlin">(UTC+01:00) Europe/Berlin</li><li value="Europe/Bratislava" title="(UTC+01:00) Europe/Bratislava">(UTC+01:00) Europe/Bratislava</li><li value="Europe/Brussels" title="(UTC+01:00) Europe/Brussels">(UTC+01:00) Europe/Brussels</li><li value="Europe/Budapest" title="(UTC+01:00) Europe/Budapest">(UTC+01:00) Europe/Budapest</li><li value="Europe/Busingen" title="(UTC+01:00) Europe/Busingen">(UTC+01:00) Europe/Busingen</li><li value="Europe/Copenhagen" title="(UTC+01:00) Europe/Copenhagen">(UTC+01:00) Europe/Copenhagen</li><li value="Europe/Gibraltar" title="(UTC+01:00) Europe/Gibraltar">(UTC+01:00) Europe/Gibraltar</li><li value="Europe/Ljubljana" title="(UTC+01:00) Europe/Ljubljana">(UTC+01:00) Europe/Ljubljana</li><li value="Europe/Luxembourg" title="(UTC+01:00) Europe/Luxembourg">(UTC+01:00) Europe/Luxembourg</li><li value="Europe/Madrid" title="(UTC+01:00) Europe/Madrid">(UTC+01:00) Europe/Madrid</li><li value="Europe/Malta" title="(UTC+01:00) Europe/Malta">(UTC+01:00) Europe/Malta</li><li value="Europe/Monaco" title="(UTC+01:00) Europe/Monaco">(UTC+01:00) Europe/Monaco</li><li value="Europe/Oslo" title="(UTC+01:00) Europe/Oslo">(UTC+01:00) Europe/Oslo</li><li value="Europe/Paris" title="(UTC+01:00) Europe/Paris">(UTC+01:00) Europe/Paris</li><li value="Europe/Podgorica" title="(UTC+01:00) Europe/Podgorica">(UTC+01:00) Europe/Podgorica</li><li value="Europe/Prague" title="(UTC+01:00) Europe/Prague">(UTC+01:00) Europe/Prague</li><li value="Europe/Rome" title="(UTC+01:00) Europe/Rome">(UTC+01:00) Europe/Rome</li><li value="Europe/San_Marino" title="(UTC+01:00) Europe/San_Marino">(UTC+01:00) Europe/San_Marino</li><li value="Europe/Sarajevo" title="(UTC+01:00) Europe/Sarajevo">(UTC+01:00) Europe/Sarajevo</li><li value="Europe/Skopje" title="(UTC+01:00) Europe/Skopje">(UTC+01:00) Europe/Skopje</li><li value="Europe/Stockholm" title="(UTC+01:00) Europe/Stockholm">(UTC+01:00) Europe/Stockholm</li><li value="Europe/Tirane" title="(UTC+01:00) Europe/Tirane">(UTC+01:00) Europe/Tirane</li><li value="Europe/Vaduz" title="(UTC+01:00) Europe/Vaduz">(UTC+01:00) Europe/Vaduz</li><li value="Europe/Vatican" title="(UTC+01:00) Europe/Vatican">(UTC+01:00) Europe/Vatican</li><li value="Europe/Vienna" title="(UTC+01:00) Europe/Vienna">(UTC+01:00) Europe/Vienna</li><li value="Europe/Warsaw" title="(UTC+01:00) Europe/Warsaw">(UTC+01:00) Europe/Warsaw</li><li value="Europe/Zagreb" title="(UTC+01:00) Europe/Zagreb">(UTC+01:00) Europe/Zagreb</li><li value="Europe/Zurich" title="(UTC+01:00) Europe/Zurich">(UTC+01:00) Europe/Zurich</li><li value="Africa/Blantyre" title="(UTC+02:00) Africa/Blantyre">(UTC+02:00) Africa/Blantyre</li><li value="Africa/Bujumbura" title="(UTC+02:00) Africa/Bujumbura">(UTC+02:00) Africa/Bujumbura</li><li value="Africa/Cairo" title="(UTC+02:00) Africa/Cairo">(UTC+02:00) Africa/Cairo</li><li value="Africa/Gaborone" title="(UTC+02:00) Africa/Gaborone">(UTC+02:00) Africa/Gaborone</li><li value="Africa/Harare" title="(UTC+02:00) Africa/Harare">(UTC+02:00) Africa/Harare</li><li value="Africa/Johannesburg" title="(UTC+02:00) Africa/Johannesburg">(UTC+02:00) Africa/Johannesburg</li><li value="Africa/Juba" title="(UTC+02:00) Africa/Juba">(UTC+02:00) Africa/Juba</li><li value="Africa/Khartoum" title="(UTC+02:00) Africa/Khartoum">(UTC+02:00) Africa/Khartoum</li><li value="Africa/Kigali" title="(UTC+02:00) Africa/Kigali">(UTC+02:00) Africa/Kigali</li><li value="Africa/Lubumbashi" title="(UTC+02:00) Africa/Lubumbashi">(UTC+02:00) Africa/Lubumbashi</li><li value="Africa/Lusaka" title="(UTC+02:00) Africa/Lusaka">(UTC+02:00) Africa/Lusaka</li><li value="Africa/Maputo" title="(UTC+02:00) Africa/Maputo">(UTC+02:00) Africa/Maputo</li><li value="Africa/Maseru" title="(UTC+02:00) Africa/Maseru">(UTC+02:00) Africa/Maseru</li><li value="Africa/Mbabane" title="(UTC+02:00) Africa/Mbabane">(UTC+02:00) Africa/Mbabane</li><li value="Africa/Tripoli" title="(UTC+02:00) Africa/Tripoli">(UTC+02:00) Africa/Tripoli</li><li value="Africa/Windhoek" title="(UTC+02:00) Africa/Windhoek">(UTC+02:00) Africa/Windhoek</li><li value="Asia/Beirut" title="(UTC+02:00) Asia/Beirut">(UTC+02:00) Asia/Beirut</li><li value="Asia/Famagusta" title="(UTC+02:00) Asia/Famagusta">(UTC+02:00) Asia/Famagusta</li><li value="Asia/Gaza" title="(UTC+02:00) Asia/Gaza">(UTC+02:00) Asia/Gaza</li><li value="Asia/Hebron" title="(UTC+02:00) Asia/Hebron">(UTC+02:00) Asia/Hebron</li><li value="Asia/Jerusalem" title="(UTC+02:00) Asia/Jerusalem">(UTC+02:00) Asia/Jerusalem</li><li value="Asia/Nicosia" title="(UTC+02:00) Asia/Nicosia">(UTC+02:00) Asia/Nicosia</li><li value="Europe/Athens" title="(UTC+02:00) Europe/Athens">(UTC+02:00) Europe/Athens</li><li value="Europe/Bucharest" title="(UTC+02:00) Europe/Bucharest">(UTC+02:00) Europe/Bucharest</li><li value="Europe/Chisinau" title="(UTC+02:00) Europe/Chisinau">(UTC+02:00) Europe/Chisinau</li><li value="Europe/Helsinki" title="(UTC+02:00) Europe/Helsinki">(UTC+02:00) Europe/Helsinki</li><li value="Europe/Kaliningrad" title="(UTC+02:00) Europe/Kaliningrad">(UTC+02:00) Europe/Kaliningrad</li><li value="Europe/Kyiv" title="(UTC+02:00) Europe/Kyiv">(UTC+02:00) Europe/Kyiv</li><li value="Europe/Mariehamn" title="(UTC+02:00) Europe/Mariehamn">(UTC+02:00) Europe/Mariehamn</li><li value="Europe/Riga" title="(UTC+02:00) Europe/Riga">(UTC+02:00) Europe/Riga</li><li value="Europe/Sofia" title="(UTC+02:00) Europe/Sofia">(UTC+02:00) Europe/Sofia</li><li value="Europe/Tallinn" title="(UTC+02:00) Europe/Tallinn">(UTC+02:00) Europe/Tallinn</li><li value="Europe/Vilnius" title="(UTC+02:00) Europe/Vilnius">(UTC+02:00) Europe/Vilnius</li><li value="Africa/Addis_Ababa" title="(UTC+03:00) Africa/Addis_Ababa">(UTC+03:00) Africa/Addis_Ababa</li><li value="Africa/Asmara" title="(UTC+03:00) Africa/Asmara">(UTC+03:00) Africa/Asmara</li><li value="Africa/Dar_es_Salaam" title="(UTC+03:00) Africa/Dar_es_Salaam">(UTC+03:00) Africa/Dar_es_Salaam</li><li value="Africa/Djibouti" title="(UTC+03:00) Africa/Djibouti">(UTC+03:00) Africa/Djibouti</li><li value="Africa/Kampala" title="(UTC+03:00) Africa/Kampala">(UTC+03:00) Africa/Kampala</li><li value="Africa/Mogadishu" title="(UTC+03:00) Africa/Mogadishu">(UTC+03:00) Africa/Mogadishu</li><li value="Africa/Nairobi" title="(UTC+03:00) Africa/Nairobi">(UTC+03:00) Africa/Nairobi</li><li value="Antarctica/Syowa" title="(UTC+03:00) Antarctica/Syowa">(UTC+03:00) Antarctica/Syowa</li><li value="Asia/Aden" title="(UTC+03:00) Asia/Aden">(UTC+03:00) Asia/Aden</li><li value="Asia/Amman" title="(UTC+03:00) Asia/Amman">(UTC+03:00) Asia/Amman</li><li value="Asia/Baghdad" title="(UTC+03:00) Asia/Baghdad">(UTC+03:00) Asia/Baghdad</li><li value="Asia/Bahrain" title="(UTC+03:00) Asia/Bahrain">(UTC+03:00) Asia/Bahrain</li><li value="Asia/Damascus" title="(UTC+03:00) Asia/Damascus">(UTC+03:00) Asia/Damascus</li><li value="Asia/Kuwait" title="(UTC+03:00) Asia/Kuwait">(UTC+03:00) Asia/Kuwait</li><li value="Asia/Qatar" title="(UTC+03:00) Asia/Qatar">(UTC+03:00) Asia/Qatar</li><li value="Asia/Riyadh" title="(UTC+03:00) Asia/Riyadh">(UTC+03:00) Asia/Riyadh</li><li value="Europe/Istanbul" title="(UTC+03:00) Europe/Istanbul">(UTC+03:00) Europe/Istanbul</li><li value="Europe/Kirov" title="(UTC+03:00) Europe/Kirov">(UTC+03:00) Europe/Kirov</li><li value="Europe/Minsk" title="(UTC+03:00) Europe/Minsk">(UTC+03:00) Europe/Minsk</li><li value="Europe/Moscow" title="(UTC+03:00) Europe/Moscow">(UTC+03:00) Europe/Moscow</li><li value="Europe/Simferopol" title="(UTC+03:00) Europe/Simferopol">(UTC+03:00) Europe/Simferopol</li><li value="Europe/Volgograd" title="(UTC+03:00) Europe/Volgograd">(UTC+03:00) Europe/Volgograd</li><li value="Indian/Antananarivo" title="(UTC+03:00) Indian/Antananarivo">(UTC+03:00) Indian/Antananarivo</li><li value="Indian/Comoro" title="(UTC+03:00) Indian/Comoro">(UTC+03:00) Indian/Comoro</li><li value="Indian/Mayotte" title="(UTC+03:00) Indian/Mayotte">(UTC+03:00) Indian/Mayotte</li><li value="Asia/Tehran" title="(UTC+03:30) Asia/Tehran">(UTC+03:30) Asia/Tehran</li><li value="Asia/Baku" title="(UTC+04:00) Asia/Baku">(UTC+04:00) Asia/Baku</li><li value="Asia/Dubai" title="(UTC+04:00) Asia/Dubai">(UTC+04:00) Asia/Dubai</li><li value="Asia/Muscat" title="(UTC+04:00) Asia/Muscat">(UTC+04:00) Asia/Muscat</li><li value="Asia/Tbilisi" title="(UTC+04:00) Asia/Tbilisi">(UTC+04:00) Asia/Tbilisi</li><li value="Asia/Yerevan" title="(UTC+04:00) Asia/Yerevan">(UTC+04:00) Asia/Yerevan</li><li value="Europe/Astrakhan" title="(UTC+04:00) Europe/Astrakhan">(UTC+04:00) Europe/Astrakhan</li><li value="Europe/Samara" title="(UTC+04:00) Europe/Samara">(UTC+04:00) Europe/Samara</li><li value="Europe/Saratov" title="(UTC+04:00) Europe/Saratov">(UTC+04:00) Europe/Saratov</li><li value="Europe/Ulyanovsk" title="(UTC+04:00) Europe/Ulyanovsk">(UTC+04:00) Europe/Ulyanovsk</li><li value="Indian/Mahe" title="(UTC+04:00) Indian/Mahe">(UTC+04:00) Indian/Mahe</li><li value="Indian/Mauritius" title="(UTC+04:00) Indian/Mauritius">(UTC+04:00) Indian/Mauritius</li><li value="Indian/Reunion" title="(UTC+04:00) Indian/Reunion">(UTC+04:00) Indian/Reunion</li><li value="Asia/Kabul" title="(UTC+04:30) Asia/Kabul">(UTC+04:30) Asia/Kabul</li><li value="Antarctica/Mawson" title="(UTC+05:00) Antarctica/Mawson">(UTC+05:00) Antarctica/Mawson</li><li value="Antarctica/Vostok" title="(UTC+05:00) Antarctica/Vostok">(UTC+05:00) Antarctica/Vostok</li><li value="Asia/Almaty" title="(UTC+05:00) Asia/Almaty">(UTC+05:00) Asia/Almaty</li><li value="Asia/Aqtau" title="(UTC+05:00) Asia/Aqtau">(UTC+05:00) Asia/Aqtau</li><li value="Asia/Aqtobe" title="(UTC+05:00) Asia/Aqtobe">(UTC+05:00) Asia/Aqtobe</li><li value="Asia/Ashgabat" title="(UTC+05:00) Asia/Ashgabat">(UTC+05:00) Asia/Ashgabat</li><li value="Asia/Atyrau" title="(UTC+05:00) Asia/Atyrau">(UTC+05:00) Asia/Atyrau</li><li value="Asia/Dushanbe" title="(UTC+05:00) Asia/Dushanbe">(UTC+05:00) Asia/Dushanbe</li><li value="Asia/Karachi" title="(UTC+05:00) Asia/Karachi">(UTC+05:00) Asia/Karachi</li><li value="Asia/Oral" title="(UTC+05:00) Asia/Oral">(UTC+05:00) Asia/Oral</li><li value="Asia/Qostanay" title="(UTC+05:00) Asia/Qostanay">(UTC+05:00) Asia/Qostanay</li><li value="Asia/Qyzylorda" title="(UTC+05:00) Asia/Qyzylorda">(UTC+05:00) Asia/Qyzylorda</li><li value="Asia/Samarkand" title="(UTC+05:00) Asia/Samarkand">(UTC+05:00) Asia/Samarkand</li><li value="Asia/Tashkent" title="(UTC+05:00) Asia/Tashkent">(UTC+05:00) Asia/Tashkent</li><li value="Asia/Yekaterinburg" title="(UTC+05:00) Asia/Yekaterinburg">(UTC+05:00) Asia/Yekaterinburg</li><li value="Indian/Kerguelen" title="(UTC+05:00) Indian/Kerguelen">(UTC+05:00) Indian/Kerguelen</li><li value="Indian/Maldives" title="(UTC+05:00) Indian/Maldives">(UTC+05:00) Indian/Maldives</li><li value="Asia/Colombo" title="(UTC+05:30) Asia/Colombo">(UTC+05:30) Asia/Colombo</li><li value="Asia/Kolkata" title="(UTC+05:30) Asia/Kolkata">(UTC+05:30) Asia/Kolkata</li><li value="Asia/Kathmandu" title="(UTC+05:45) Asia/Kathmandu">(UTC+05:45) Asia/Kathmandu</li><li value="Asia/Bishkek" title="(UTC+06:00) Asia/Bishkek">(UTC+06:00) Asia/Bishkek</li><li value="Asia/Dhaka" title="(UTC+06:00) Asia/Dhaka">(UTC+06:00) Asia/Dhaka</li><li value="Asia/Omsk" title="(UTC+06:00) Asia/Omsk">(UTC+06:00) Asia/Omsk</li><li value="Asia/Thimphu" title="(UTC+06:00) Asia/Thimphu">(UTC+06:00) Asia/Thimphu</li><li value="Asia/Urumqi" title="(UTC+06:00) Asia/Urumqi">(UTC+06:00) Asia/Urumqi</li><li value="Indian/Chagos" title="(UTC+06:00) Indian/Chagos">(UTC+06:00) Indian/Chagos</li><li value="Asia/Yangon" title="(UTC+06:30) Asia/Yangon">(UTC+06:30) Asia/Yangon</li><li value="Indian/Cocos" title="(UTC+06:30) Indian/Cocos">(UTC+06:30) Indian/Cocos</li><li value="Antarctica/Davis" title="(UTC+07:00) Antarctica/Davis">(UTC+07:00) Antarctica/Davis</li><li value="Asia/Bangkok" title="(UTC+07:00) Asia/Bangkok">(UTC+07:00) Asia/Bangkok</li><li value="Asia/Barnaul" title="(UTC+07:00) Asia/Barnaul">(UTC+07:00) Asia/Barnaul</li><li value="Asia/Hovd" title="(UTC+07:00) Asia/Hovd">(UTC+07:00) Asia/Hovd</li><li value="Asia/Ho_Chi_Minh" title="(UTC+07:00) Asia/Ho_Chi_Minh">(UTC+07:00) Asia/Ho_Chi_Minh</li><li value="Asia/Jakarta" title="(UTC+07:00) Asia/Jakarta">(UTC+07:00) Asia/Jakarta</li><li value="Asia/Krasnoyarsk" title="(UTC+07:00) Asia/Krasnoyarsk">(UTC+07:00) Asia/Krasnoyarsk</li><li value="Asia/Novokuznetsk" title="(UTC+07:00) Asia/Novokuznetsk">(UTC+07:00) Asia/Novokuznetsk</li><li value="Asia/Novosibirsk" title="(UTC+07:00) Asia/Novosibirsk">(UTC+07:00) Asia/Novosibirsk</li><li value="Asia/Phnom_Penh" title="(UTC+07:00) Asia/Phnom_Penh">(UTC+07:00) Asia/Phnom_Penh</li><li value="Asia/Pontianak" title="(UTC+07:00) Asia/Pontianak">(UTC+07:00) Asia/Pontianak</li><li value="Asia/Tomsk" title="(UTC+07:00) Asia/Tomsk">(UTC+07:00) Asia/Tomsk</li><li value="Asia/Vientiane" title="(UTC+07:00) Asia/Vientiane">(UTC+07:00) Asia/Vientiane</li><li value="Indian/Christmas" title="(UTC+07:00) Indian/Christmas">(UTC+07:00) Indian/Christmas</li><li value="Antarctica/Casey" title="(UTC+08:00) Antarctica/Casey">(UTC+08:00) Antarctica/Casey</li><li value="Asia/Brunei" title="(UTC+08:00) Asia/Brunei">(UTC+08:00) Asia/Brunei</li><li value="Asia/Hong_Kong" title="(UTC+08:00) Asia/Hong_Kong">(UTC+08:00) Asia/Hong_Kong</li><li value="Asia/Irkutsk" title="(UTC+08:00) Asia/Irkutsk">(UTC+08:00) Asia/Irkutsk</li><li value="Asia/Kuala_Lumpur" title="(UTC+08:00) Asia/Kuala_Lumpur">(UTC+08:00) Asia/Kuala_Lumpur</li><li value="Asia/Kuching" title="(UTC+08:00) Asia/Kuching">(UTC+08:00) Asia/Kuching</li><li value="Asia/Macau" title="(UTC+08:00) Asia/Macau">(UTC+08:00) Asia/Macau</li><li value="Asia/Makassar" title="(UTC+08:00) Asia/Makassar">(UTC+08:00) Asia/Makassar</li><li value="Asia/Manila" title="(UTC+08:00) Asia/Manila">(UTC+08:00) Asia/Manila</li><li value="Asia/Shanghai" title="(UTC+08:00) Asia/Shanghai">(UTC+08:00) Asia/Shanghai</li><li value="Asia/Singapore" title="(UTC+08:00) Asia/Singapore">(UTC+08:00) Asia/Singapore</li><li value="Asia/Taipei" title="(UTC+08:00) Asia/Taipei">(UTC+08:00) Asia/Taipei</li><li value="Asia/Ulaanbaatar" title="(UTC+08:00) Asia/Ulaanbaatar">(UTC+08:00) Asia/Ulaanbaatar</li><li value="Australia/Perth" title="(UTC+08:00) Australia/Perth">(UTC+08:00) Australia/Perth</li><li value="Australia/Eucla" title="(UTC+08:45) Australia/Eucla">(UTC+08:45) Australia/Eucla</li><li value="Asia/Chita" title="(UTC+09:00) Asia/Chita">(UTC+09:00) Asia/Chita</li><li value="Asia/Dili" title="(UTC+09:00) Asia/Dili">(UTC+09:00) Asia/Dili</li><li value="Asia/Jayapura" title="(UTC+09:00) Asia/Jayapura">(UTC+09:00) Asia/Jayapura</li><li value="Asia/Khandyga" title="(UTC+09:00) Asia/Khandyga">(UTC+09:00) Asia/Khandyga</li><li value="Asia/Pyongyang" title="(UTC+09:00) Asia/Pyongyang">(UTC+09:00) Asia/Pyongyang</li><li value="Asia/Seoul" title="(UTC+09:00) Asia/Seoul">(UTC+09:00) Asia/Seoul</li><li value="Asia/Tokyo" title="(UTC+09:00) Asia/Tokyo">(UTC+09:00) Asia/Tokyo</li><li value="Asia/Yakutsk" title="(UTC+09:00) Asia/Yakutsk">(UTC+09:00) Asia/Yakutsk</li><li value="Pacific/Palau" title="(UTC+09:00) Pacific/Palau">(UTC+09:00) Pacific/Palau</li><li value="Australia/Darwin" title="(UTC+09:30) Australia/Darwin">(UTC+09:30) Australia/Darwin</li><li value="Antarctica/DumontDUrville" title="(UTC+10:00) Antarctica/DumontDUrville">(UTC+10:00) Antarctica/DumontDUrville</li><li value="Asia/Ust-Nera" title="(UTC+10:00) Asia/Ust-Nera">(UTC+10:00) Asia/Ust-Nera</li><li value="Asia/Vladivostok" title="(UTC+10:00) Asia/Vladivostok">(UTC+10:00) Asia/Vladivostok</li><li value="Australia/Brisbane" title="(UTC+10:00) Australia/Brisbane">(UTC+10:00) Australia/Brisbane</li><li value="Australia/Lindeman" title="(UTC+10:00) Australia/Lindeman">(UTC+10:00) Australia/Lindeman</li><li value="Pacific/Chuuk" title="(UTC+10:00) Pacific/Chuuk">(UTC+10:00) Pacific/Chuuk</li><li value="Pacific/Guam" title="(UTC+10:00) Pacific/Guam">(UTC+10:00) Pacific/Guam</li><li value="Pacific/Port_Moresby" title="(UTC+10:00) Pacific/Port_Moresby">(UTC+10:00) Pacific/Port_Moresby</li><li value="Pacific/Saipan" title="(UTC+10:00) Pacific/Saipan">(UTC+10:00) Pacific/Saipan</li><li value="Australia/Adelaide" title="(UTC+10:30) Australia/Adelaide">(UTC+10:30) Australia/Adelaide</li><li value="Australia/Broken_Hill" title="(UTC+10:30) Australia/Broken_Hill">(UTC+10:30) Australia/Broken_Hill</li><li value="Antarctica/Macquarie" title="(UTC+11:00) Antarctica/Macquarie">(UTC+11:00) Antarctica/Macquarie</li><li value="Asia/Magadan" title="(UTC+11:00) Asia/Magadan">(UTC+11:00) Asia/Magadan</li><li value="Asia/Sakhalin" title="(UTC+11:00) Asia/Sakhalin">(UTC+11:00) Asia/Sakhalin</li><li value="Asia/Srednekolymsk" title="(UTC+11:00) Asia/Srednekolymsk">(UTC+11:00) Asia/Srednekolymsk</li><li value="Australia/Hobart" title="(UTC+11:00) Australia/Hobart">(UTC+11:00) Australia/Hobart</li><li value="Australia/Lord_Howe" title="(UTC+11:00) Australia/Lord_Howe">(UTC+11:00) Australia/Lord_Howe</li><li value="Australia/Melbourne" title="(UTC+11:00) Australia/Melbourne">(UTC+11:00) Australia/Melbourne</li><li value="Australia/Sydney" title="(UTC+11:00) Australia/Sydney">(UTC+11:00) Australia/Sydney</li><li value="Pacific/Bougainville" title="(UTC+11:00) Pacific/Bougainville">(UTC+11:00) Pacific/Bougainville</li><li value="Pacific/Efate" title="(UTC+11:00) Pacific/Efate">(UTC+11:00) Pacific/Efate</li><li value="Pacific/Guadalcanal" title="(UTC+11:00) Pacific/Guadalcanal">(UTC+11:00) Pacific/Guadalcanal</li><li value="Pacific/Kosrae" title="(UTC+11:00) Pacific/Kosrae">(UTC+11:00) Pacific/Kosrae</li><li value="Pacific/Noumea" title="(UTC+11:00) Pacific/Noumea">(UTC+11:00) Pacific/Noumea</li><li value="Pacific/Pohnpei" title="(UTC+11:00) Pacific/Pohnpei">(UTC+11:00) Pacific/Pohnpei</li><li value="Asia/Anadyr" title="(UTC+12:00) Asia/Anadyr">(UTC+12:00) Asia/Anadyr</li><li value="Asia/Kamchatka" title="(UTC+12:00) Asia/Kamchatka">(UTC+12:00) Asia/Kamchatka</li><li value="Pacific/Fiji" title="(UTC+12:00) Pacific/Fiji">(UTC+12:00) Pacific/Fiji</li><li value="Pacific/Funafuti" title="(UTC+12:00) Pacific/Funafuti">(UTC+12:00) Pacific/Funafuti</li><li value="Pacific/Kwajalein" title="(UTC+12:00) Pacific/Kwajalein">(UTC+12:00) Pacific/Kwajalein</li><li value="Pacific/Majuro" title="(UTC+12:00) Pacific/Majuro">(UTC+12:00) Pacific/Majuro</li><li value="Pacific/Nauru" title="(UTC+12:00) Pacific/Nauru">(UTC+12:00) Pacific/Nauru</li><li value="Pacific/Norfolk" title="(UTC+12:00) Pacific/Norfolk">(UTC+12:00) Pacific/Norfolk</li><li value="Pacific/Tarawa" title="(UTC+12:00) Pacific/Tarawa">(UTC+12:00) Pacific/Tarawa</li><li value="Pacific/Wake" title="(UTC+12:00) Pacific/Wake">(UTC+12:00) Pacific/Wake</li><li value="Pacific/Wallis" title="(UTC+12:00) Pacific/Wallis">(UTC+12:00) Pacific/Wallis</li><li value="Antarctica/McMurdo" title="(UTC+13:00) Antarctica/McMurdo">(UTC+13:00) Antarctica/McMurdo</li><li value="Pacific/Apia" title="(UTC+13:00) Pacific/Apia">(UTC+13:00) Pacific/Apia</li><li value="Pacific/Auckland" title="(UTC+13:00) Pacific/Auckland">(UTC+13:00) Pacific/Auckland</li><li value="Pacific/Fakaofo" title="(UTC+13:00) Pacific/Fakaofo">(UTC+13:00) Pacific/Fakaofo</li><li value="Pacific/Kanton" title="(UTC+13:00) Pacific/Kanton">(UTC+13:00) Pacific/Kanton</li><li value="Pacific/Tongatapu" title="(UTC+13:00) Pacific/Tongatapu">(UTC+13:00) Pacific/Tongatapu</li><li value="Pacific/Chatham" title="(UTC+13:45) Pacific/Chatham">(UTC+13:45) Pacific/Chatham</li><li value="Pacific/Kiritimati" title="(UTC+14:00) Pacific/Kiritimati">(UTC+14:00) Pacific/Kiritimati</li></ul></z-select></div><label>Schedule</label><div class="form-field"><ul id="schedule_mode" class="radio-list-control"><li><input type="radio" id="schedule_mode_0" name="schedule_mode" value="0" checked="checked"><label for="schedule_mode_0">24x7</label></li><li><input type="radio" id="schedule_mode_1" name="schedule_mode" value="1"><label for="schedule_mode_1">Custom</label></li></ul></div><div class="form-field" id="schedule" style="display: none;"><div class="table-forms-separator"><table style="min-width: 453px;"><tbody><tr><td><input type="checkbox" id="schedule_enabled_0" name="schedule_enabled[0]" value="0" class="checkbox-radio"><label for="schedule_enabled_0"><span></span>Sunday</label></td><td><input type="text" id="schedule_periods_0" name="schedule_periods[0]" value="" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..." disabled=""></td></tr><tr><td><input type="checkbox" id="schedule_enabled_1" name="schedule_enabled[1]" value="1" class="checkbox-radio" checked="checked"><label for="schedule_enabled_1"><span></span>Monday</label></td><td><input type="text" id="schedule_periods_1" name="schedule_periods[1]" value="8:00-17:00" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..."></td></tr><tr><td><input type="checkbox" id="schedule_enabled_2" name="schedule_enabled[2]" value="2" class="checkbox-radio" checked="checked"><label for="schedule_enabled_2"><span></span>Tuesday</label></td><td><input type="text" id="schedule_periods_2" name="schedule_periods[2]" value="8:00-17:00" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..."></td></tr><tr><td><input type="checkbox" id="schedule_enabled_3" name="schedule_enabled[3]" value="3" class="checkbox-radio" checked="checked"><label for="schedule_enabled_3"><span></span>Wednesday</label></td><td><input type="text" id="schedule_periods_3" name="schedule_periods[3]" value="8:00-17:00" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..."></td></tr><tr><td><input type="checkbox" id="schedule_enabled_4" name="schedule_enabled[4]" value="4" class="checkbox-radio" checked="checked"><label for="schedule_enabled_4"><span></span>Thursday</label></td><td><input type="text" id="schedule_periods_4" name="schedule_periods[4]" value="8:00-17:00" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..."></td></tr><tr><td><input type="checkbox" id="schedule_enabled_5" name="schedule_enabled[5]" value="5" class="checkbox-radio" checked="checked"><label for="schedule_enabled_5"><span></span>Friday</label></td><td><input type="text" id="schedule_periods_5" name="schedule_periods[5]" value="8:00-17:00" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..."></td></tr><tr><td><input type="checkbox" id="schedule_enabled_6" name="schedule_enabled[6]" value="6" class="checkbox-radio"><label for="schedule_enabled_6"><span></span>Saturday</label></td><td><input type="text" id="schedule_periods_6" name="schedule_periods[6]" value="" maxlength="255" style="width: 270px;" placeholder="8:00-17:00, ..." disabled=""></td></tr></tbody></table></div></div><label for="effective_date" class="form-label-asterisk">Effective date</label><div class="form-field"><div class="calendar-control"><input type="text" id="effective_date" name="effective_date" value="2025-11-07" maxlength="255" placeholder="YYYY-MM-DD"><button type="button" id="effective_date_calendar" name="effective_date_calendar" class="btn-icon zi-calendar" onclick="toggleCalendar(this, &quot;effective_date&quot;, &quot;Y-m-d&quot;);"></button></div></div><label class="form-label-asterisk">Service tags</label><div class="form-field"><div class="table-forms-separator"><table id="service-tags" style="min-width: 453px;"><thead><tr class="grey"><th>Name</th><th>Operation</th><th>Value</th><th>Action</th></tr></thead><tbody><tr class="form_row"><td><input type="text" id="service_tags_0_tag" name="service_tags[0][tag]" value="" maxlength="255" placeholder="tag" style="width: 150px;"></td><td><z-select value="0" name="service_tags[0][operator]" tabindex="-1" width="91" style="width: 91px;"><button type="button" class="focusable">Equals</button><input name="service_tags[0][operator]" type="hidden" value="0"><ul class="list"><li value="0" title="Equals">Equals</li><li value="2" title="Contains">Contains</li></ul></z-select></td><td><input type="text" id="service_tags_0_value" name="service_tags[0][value]" value="" maxlength="255" placeholder="value" style="width: 150px;"></td><td><button type="button" class="btn-link element-table-remove">Remove</button></td></tr><tr><td colspan="4"><button type="button" class="btn-link element-table-add">Add</button></td></tr></tbody></table><template id="service-tag-row-tmpl"><tr class="form_row"><td><input type="text" id="service_tags_#{rowNum}_tag" name="service_tags[#{rowNum}][tag]" value="#{tag}" maxlength="255" placeholder="tag" style="width: 150px;"></td><td><z-select value="0" name="service_tags[#{rowNum}][operator]" data-options="[{&quot;value&quot;:0,&quot;label&quot;:&quot;Equals&quot;},{&quot;value&quot;:2,&quot;label&quot;:&quot;Contains&quot;}]" tabindex="-1"></z-select></td><td><input type="text" id="service_tags_#{rowNum}_value" name="service_tags[#{rowNum}][value]" value="#{value}" maxlength="255" placeholder="value" style="width: 150px;"></td><td><button type="button" class="btn-link element-table-remove">Remove</button></td></tr></template></div></div><label for="description">Description</label><div class="form-field"><textarea id="description" name="description" rows="7" style="width: 453px;" maxlength="65535"></textarea></div><label for="status">Enabled</label><div class="form-field"><input type="checkbox" id="status" name="status" value="1" class="checkbox-radio" checked="checked"><label for="status"><span></span></label></div></div></div><div id="excluded-downtimes-tab" style="display: none" aria-hidden="true" aria-labelledby="tab_excluded-downtimes-tab" role="tabpanel" class="ui-tabs-panel ui-corner-bottom ui-widget-content"><div class="form-grid"><label>Excluded downtimes</label><div class="form-field"><div class="table-forms-separator" style="min-width: 540px;"><table id="excluded-downtimes"><thead><tr class="grey"><th>Start time</th><th>Duration</th><th>Name</th><th>Action</th></tr></thead><tbody></tbody><tfoot><tr><td colspan="4"><button type="button" class="btn-link js-add">Add</button></td></tr></tfoot></table></div></div></div></div></div><script>jQuery(function($){
			sla_edit_popup.init({"slaid":null,"service_tags":[{"tag":"","operator":0,"value":""}],"excluded_downtimes":[]});
		});</script></form></div><div class="overlay-dialogue-footer"><script>jQuery("#tabs")
				.tabs({create: function() {sessionStorage.setItem(ZBX_SESSION_NAME + ":tab.tabs", 0);},disabled: [],active: 0,activate: function(event, ui) {sessionStorage.setItem(ZBX_SESSION_NAME + ":tab.tabs", ui.newTab.index().toString());jQuery.cookie("tab", ui.newTab.index().toString());}}).parent().on("submit", function() {jQuery.cookie("tab", sessionStorage.getItem(ZBX_SESSION_NAME + ":tab.tabs") || 0);});
try { new TabIndicators("tabs"); } catch(e) { }
window.sla_edit_popup = new class {

	init({slaid, service_tags, excluded_downtimes}) {
		this._initTemplates();

		this.slaid = slaid;

		this.overlay = overlays_stack.getById('sla_edit');
		this.dialogue = this.overlay.$dialogue[0];
		this.form = this.overlay.$dialogue.$body[0].querySelector('form');
		this.footer = this.overlay.$dialogue.$footer[0];

		for (const excluded_downtime of excluded_downtimes) {
			this._addExcludedDowntime(excluded_downtime);
		}

		// Update form field state according to the form data.

		for (const element of document.querySelectorAll('#schedule_mode input[type="radio"')) {
			element.addEventListener('change', () => this._update());
		}

		for (const element of document.querySelectorAll('#schedule input[type="checkbox"]')) {
			element.addEventListener('change', () => this._update());
		}

		// Setup Problem tags.

		const $service_tags = jQuery(document.getElementById('service-tags'));

		$service_tags.dynamicRows({
			template: '#service-tag-row-tmpl',
			rows: service_tags,
			allow_empty: true
		});

		// Setup Excluded downtimes.
		document
			.getElementById('excluded-downtimes')
			.addEventListener('click', (e) => {
				if (e.target.classList.contains('js-add')) {
					this._editExcludedDowntime();
				}
				else if (e.target.classList.contains('js-edit')) {
					this._editExcludedDowntime(e.target.closest('tr'));
				}
				else if (e.target.classList.contains('js-remove')) {
					e.target.closest('tr').remove();
				}
			});

		this._update();

		this.form.style.display = '';
		this.overlay.recoverFocus();
	}

	_initTemplates() {
		this.excluded_downtime_template = new Template(`
			<tr data-row_index="#{row_index}">
				<td>
					#{start_time}
					<input type="hidden" name="excluded_downtimes[#{row_index}][name]" value="#{name}">
					<input type="hidden" name="excluded_downtimes[#{row_index}][period_from]" value="#{period_from}">
					<input type="hidden" name="excluded_downtimes[#{row_index}][period_to]" value="#{period_to}">
				</td>
				<td>#{duration}</td>
				<td class="wordwrap" style="max-width: 540px;">#{name}</td>
				<td>
					<ul class="hor-list">
						<li>
							<button type="button" class="btn-link js-edit">Edit</button>
						</li>
						<li>
							<button type="button" class="btn-link js-remove">Remove</button>
						</li>
					</ul>
				</td>
			</tr>
		`);
	}

	_update() {
		const schedule = document.getElementById('schedule');
		const schedule_mode = document.querySelector('#schedule_mode input:checked').value;

		schedule.style.display = schedule_mode == 1 ? '' : 'none';

		for (const element of schedule.querySelectorAll('input[type="checkbox"]')) {
			schedule.querySelector(`input[name="schedule_periods[${element.value}]"]`).disabled = !element.checked;
		}
	}

	_editExcludedDowntime(row = null) {
		let popup_params;

		if (row !== null) {
			const row_index = row.dataset.row_index;

			popup_params = {
				edit: '1',
				row_index,
				name: row.querySelector(`[name="excluded_downtimes[${row_index}][name]"`).value,
				period_from: row.querySelector(`[name="excluded_downtimes[${row_index}][period_from]"`).value,
				period_to: row.querySelector(`[name="excluded_downtimes[${row_index}][period_to]"`).value
			};
		}
		else {
			let row_index = 0;

			while (document.querySelector(`#excluded-downtimes [data-row_index="${row_index}"]`) !== null) {
				row_index++;
			}

			popup_params = {row_index};
		}

		const overlay = PopUp('popup.sla.excludeddowntime.edit', popup_params, {
			dialogueid: 'sla_excluded_downtime_edit',
			dialogue_class: 'modal-popup-medium'
		});

		overlay.$dialogue[0].addEventListener('dialogue.submit', (e) => {
			if (row !== null) {
				this._updateExcludedDowntime(row, e.detail)
			}
			else {
				this._addExcludedDowntime(e.detail);
			}
		});
	}

	_addExcludedDowntime(excluded_downtime) {
		document
			.querySelector('#excluded-downtimes tbody')
			.insertAdjacentHTML('beforeend', this.excluded_downtime_template.evaluate(excluded_downtime));
	}

	_updateExcludedDowntime(row, excluded_downtime) {
		row.insertAdjacentHTML('afterend', this.excluded_downtime_template.evaluate(excluded_downtime));
		row.remove();
	}

	clone({title, buttons}) {
		this.slaid = null;

		this.overlay.unsetLoading();
		this.overlay.setProperties({title, buttons});
		this.overlay.recoverFocus();
		this.overlay.containFocus();
	}

	delete() {
		const curl = new Curl('zabbix.php');
		curl.setArgument('action', 'sla.delete');
		curl.setArgument(CSRF_TOKEN_NAME, "dae1472721fb0a909ec66b8b5f1b4e555152e0a16afa8018e31ab7745fbbe3ed");

		this._post(curl.getUrl(), {slaids: [this.slaid]}, (response) => {
			overlayDialogueDestroy(this.overlay.dialogueid);

			this.dialogue.dispatchEvent(new CustomEvent('dialogue.submit', {detail: response.success}));
		});
	}

	submit() {
		const fields = getFormFields(this.form);

		if (this.slaid !== null) {
			fields.slaid = this.slaid;
		}

		fields.name = fields.name.trim();
		fields.slo = fields.slo.trim();

		if ('service_tags' in fields) {
			for (const service_tag of Object.values(fields.service_tags)) {
				service_tag.tag = service_tag.tag.trim();
				service_tag.value = service_tag.value.trim();
			}
		}

		this.overlay.setLoading();

		const curl = new Curl('zabbix.php');
		curl.setArgument('action', this.slaid !== null ? 'sla.update' : 'sla.create');

		this._post(curl.getUrl(), fields, (response) => {
			overlayDialogueDestroy(this.overlay.dialogueid);

			this.dialogue.dispatchEvent(new CustomEvent('dialogue.submit', {detail: response.success}));
		});
	}

	_post(url, data, success_callback) {
		fetch(url, {
			method: 'POST',
			headers: {'Content-Type': 'application/json'},
			body: JSON.stringify(data)
		})
			.then((response) => response.json())
			.then((response) => {
				if ('error' in response) {
					throw {error: response.error};
				}

				return response;
			})
			.then(success_callback)
			.catch((exception) => {
				for (const element of this.form.parentNode.children) {
					if (element.matches('.msg-good, .msg-bad, .msg-warning')) {
						element.parentNode.removeChild(element);
					}
				}

				let title, messages;

				if (typeof exception === 'object' && 'error' in exception) {
					title = exception.error.title;
					messages = exception.error.messages;
				}
				else {
					messages = ["Unexpected server error."];
				}

				const message_box = makeMessageBox('bad', messages, title)[0];

				this.form.parentNode.insertBefore(message_box, this.form);
			})
			.finally(() => {
				this.overlay.unsetLoading();
			});
	}
};
</script><button type="button" class="js-add">Add</button><button type="button" class="btn-alt js-cancel">Cancel</button></div></div>
```


SLA Report Page copy from browser:
```
SLA report
Filter
SLA
WIN-SERVER SLA
Select
Service
type here to search
Select
From
YYYY-MM-DD

To
YYYY-MM-DD

ApplyReset
Service
SLO	2025-10-19	2025-10-20	2025-10-21	2025-10-22	2025-10-23	2025-10-24	2025-10-25	2025-10-26	2025-10-27	2025-10-28	2025-10-29	2025-10-30	2025-10-31	2025-11-01	2025-11-02	2025-11-03	2025-11-04	2025-11-05	2025-11-06	2025-11-07
WINDOWS-SERVER availability	100%	100	100	100	100	100	100	100	100	100	100	100	100	100	100	100	100	100	100	100	100
Displaying 1 of 1 found
```

SLA Report Page outer html:
```
<div class="wrapper">
<script>
	const view = new class {

		init() {
			jQuery('#filter_serviceid')
				.multiSelect('getSelectButton')
				.addEventListener('click', () => {
					this._selectService();
				});
		}

		_selectService() {
			const overlay = PopUp('popup.services', {
				title: "Service",
				multiple: 0
			}, {dialogueid: 'services', dialogue_class: 'modal-popup-generic'});

			overlay.$dialogue[0].addEventListener('dialogue.submit', (e) => {
				const data = [];

				for (const service of e.detail) {
					data.push({id: service.serviceid, name: service.name});
				}

				jQuery('#filter_serviceid').multiSelect('addData', data);
			});
		}
	};
</script>
<header class="header-title"><nav class="sidebar-nav-toggle" role="navigation" aria-label="Sidebar control"><button type="button" class="btn-icon zi-menu" title="Show sidebar" id="sidebar-button-toggle"></button></nav><div><h1 id="page-title-general">SLA report</h1></div><div class="header-doc-link"><a class="btn-icon zi-help" title="Help" target="_blank" rel="noopener noreferrer" href="https://www.zabbix.com/documentation/7.0/en/manual/web_interface/frontend_sections/services/sla_report#overview"></a></div></header><main><div data-accessible="1" class="filter-space ui-tabs ui-corner-all ui-widget ui-widget-content ui-tabs-collapsible" id="filter_690d416ce1523" data-profile-idx="web.slareport.list.filter" data-profile-idx2="0" style="" aria-label="Filter"><ul class="filter-btn-container ui-tabs-nav ui-corner-all ui-helper-reset ui-helper-clearfix ui-widget-header" role="tablist"><li role="tab" tabindex="0" class="ui-tabs-tab ui-corner-top ui-state-default ui-tab ui-tabs-active ui-state-active" aria-controls="tab_0" aria-labelledby="ui-id-1" aria-selected="true" aria-expanded="true"><a class="btn zi-filter filter-trigger ui-tabs-anchor" href="#tab_0" tabindex="-1" id="ui-id-1">Filter</a></li></ul><form method="get" action="zabbix.php" accept-charset="utf-8" name="zbx_filter"><input type="hidden" id="action" name="action" value="slareport.list"><div class="filter-container ui-tabs-panel ui-corner-bottom ui-widget-content" id="tab_0" aria-labelledby="ui-id-1" role="tabpanel" aria-hidden="false"><div class="table filter-forms"><div class="row"><div class="cell"><div class="form-grid label-width-true"><label for="filter_slaid_ms">SLA</label><div class="form-field"><div class="multiselect-control"><div id="filter_slaid" class="multiselect search-disabled" role="application" data-params="{&quot;name&quot;:&quot;filter_slaid&quot;,&quot;labels&quot;:{&quot;No matches found&quot;:&quot;No matches found&quot;,&quot;More matches found...&quot;:&quot;More matches found...&quot;,&quot;type here to search&quot;:&quot;type here to search&quot;,&quot;new&quot;:&quot;new&quot;,&quot;Select&quot;:&quot;Select&quot;},&quot;url&quot;:&quot;jsrpc.php?type=11&amp;method=multiselect.get&amp;object_name=sla&amp;enabled_only=1&quot;,&quot;data&quot;:[{&quot;name&quot;:&quot;WIN-SERVER SLA&quot;,&quot;period&quot;:&quot;0&quot;,&quot;slo&quot;:&quot;100&quot;,&quot;timezone&quot;:&quot;system&quot;,&quot;id&quot;:&quot;3&quot;}],&quot;selectedLimit&quot;:&quot;1&quot;,&quot;popup&quot;:{&quot;parameters&quot;:{&quot;srctbl&quot;:&quot;sla&quot;,&quot;srcfld1&quot;:&quot;slaid&quot;,&quot;dstfrm&quot;:&quot;zbx_filter&quot;,&quot;dstfld1&quot;:&quot;filter_slaid&quot;,&quot;enabled_only&quot;:&quot;1&quot;}}}" style="width: 300px;"><div aria-live="assertive" aria-atomic="true"></div><div class="selected"><ul class="multiselect-list"><li data-id="3" data-label="WIN-SERVER SLA"><span class="subfilter-enabled"><span title="WIN-SERVER SLA">WIN-SERVER SLA</span><span class="btn-icon zi-remove-smaller"></span></span></li></ul></div><input id="filter_slaid_ms" class="input" type="text" autocomplete="off" placeholder="" aria-label="" aria-required="false" readonly="readonly"><input type="hidden" name="filter_slaid" value="3" data-name="WIN-SERVER SLA" data-prefix=""></div><ul class="btn-split"><li><button type="button" class="btn-grey multiselect-button">Select</button></li></ul></div></div><label for="filter_serviceid_ms">Service</label><div class="form-field"><div class="multiselect-control"><div id="filter_serviceid" class="multiselect" role="application" data-params="{&quot;name&quot;:&quot;filter_serviceid&quot;,&quot;labels&quot;:{&quot;No matches found&quot;:&quot;No matches found&quot;,&quot;More matches found...&quot;:&quot;More matches found...&quot;,&quot;type here to search&quot;:&quot;type here to search&quot;,&quot;new&quot;:&quot;new&quot;,&quot;Select&quot;:&quot;Select&quot;},&quot;url&quot;:&quot;jsrpc.php?type=11&amp;method=multiselect.get&amp;object_name=services&quot;,&quot;data&quot;:[],&quot;selectedLimit&quot;:&quot;1&quot;,&quot;custom_select&quot;:true}" style="width: 300px;"><div aria-live="assertive" aria-atomic="true"></div><div class="selected"><ul class="multiselect-list"></ul></div><input id="filter_serviceid_ms" class="input" type="text" autocomplete="off" placeholder="type here to search" aria-label="Service. type here to search" aria-required="false"></div><ul class="btn-split"><li><button type="button" class="btn-grey multiselect-button">Select</button></li></ul></div></div></div></div><div class="cell"><div class="form-grid label-width-true"><label for="filter_date_from">From</label><div class="form-field"><div class="calendar-control"><input type="text" id="filter_date_from" name="filter_date_from" value="" maxlength="255" placeholder="YYYY-MM-DD"><button type="button" id="filter_date_from_calendar" name="filter_date_from_calendar" class="btn-icon zi-calendar" onclick="toggleCalendar(this, &quot;filter_date_from&quot;, &quot;Y-m-d&quot;);"></button></div></div><label for="filter_date_to">To</label><div class="form-field"><div class="calendar-control"><input type="text" id="filter_date_to" name="filter_date_to" value="" maxlength="255" placeholder="YYYY-MM-DD"><button type="button" id="filter_date_to_calendar" name="filter_date_to_calendar" class="btn-icon zi-calendar" onclick="toggleCalendar(this, &quot;filter_date_to&quot;, &quot;Y-m-d&quot;);"></button></div></div></div></div></div></div><div class="filter-forms"><button type="submit" name="filter_set" value="1" onclick="javascript: chkbxRange.clearSelectedOnFilterChange();">Apply</button><button type="button" data-url="zabbix.php?action=slareport.list&amp;filter_rst=1" class="btn-alt" onclick="javascript: chkbxRange.clearSelectedOnFilterChange();">Reset</button></div></div></form></div><script type="text/javascript">
jQuery("#filter_690d416ce1523").tabs({"collapsible":true,"active":0}).show();jQuery("[autofocus=autofocus]", jQuery("#filter_690d416ce1523")).filter(":visible").focus();jQuery("#filter_690d416ce1523").on("tabsactivate", function(e, ui) {var active = ui.newPanel.length ? jQuery(this).tabs("option", "active") + 1 : 0;updateUserProfile("web.slareport.list.filter.active", active, []);if (active) {jQuery("[autofocus=autofocus]", ui.newPanel).focus();}});
</script><form method="post" action="zabbix.php" accept-charset="utf-8" id="slareport-list" name="slareport_list"><table class="list-table" id="t690d416ce21df153536276"><thead><tr><th style="width: 15%;"><a href="zabbix.php?action=slareport.list&amp;sort=name&amp;sortorder=DESC">Service<span class="arrow-up"></span></a></th><th>SLO</th><th><z-vertical style="width: 22px; height: 61px;">2025-10-19</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-20</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-21</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-22</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-23</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-24</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-25</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-26</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-27</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-28</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-29</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-30</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-10-31</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-01</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-02</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-03</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-04</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-05</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-06</z-vertical></th><th><z-vertical style="width: 22px; height: 61px;">2025-11-07</z-vertical></th></tr></thead><tbody><tr><td class="wordbreak"><a href="zabbix.php?action=slareport.list&amp;filter_slaid=3&amp;filter_serviceid=3&amp;filter_set=1">WINDOWS-SERVER availability</a></td><td><span>100%</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td><td><span class="green">100</span></td></tr></tbody></table><div class="table-paging"><nav class="paging-btn-container" role="navigation" aria-label="Pager"><div class="table-stats">Displaying 1 of 1 found</div></nav></div></form><div hidden="" class="overlay-dialogue notif ui-draggable" style="display: none; right: 10px; top: 10px;"><div class="overlay-dialogue-header cursor-move ui-draggable-handle"><ul><li><button title="Snooze for Admin" class="btn-icon zi-bell"></button></li><li><button title="Mute for Admin" class="btn-icon zi-speaker"></button></li></ul><button title="Close" type="button" class="btn-overlay-close"></button></div><ul class="notif-body"></ul></div></main><script>jQuery(function($){
	view.init();
});</script><output id="msg-global-footer" class="msg-global-footer msg-warning" style="left: 185px; width: 1253px;"></output><footer role="contentinfo">Zabbix 7.0.12. © 2001–2025, <a class="grey link-alt" target="_blank" rel="noopener noreferrer" href="https://www.zabbix.com/">Zabbix SIA</a></footer>
<script type="text/javascript">
	$(function() {
		
		// the chkbxRange.init() method must be called after the inserted post scripts and initializing cookies
		cookie.init();
		chkbxRange.init();
	});

	/**
	 * Toggles filter state and updates title and icons accordingly.
	 *
	 * @param {string} 	idx					User profile index
	 * @param {string} 	value				Value
	 * @param {object} 	idx2				An array of IDs
	 * @param {int} 	profile_type		Profile type
	 */
	function updateUserProfile(idx, value, idx2, profile_type = PROFILE_TYPE_INT) {
		const value_fields = {
			[PROFILE_TYPE_INT]: 'value_int',
			[PROFILE_TYPE_STR]: 'value_str'
		};

		return sendAjaxData('zabbix.php?action=profile.update', {
			data: {
				idx: idx,
				[value_fields[profile_type]]: value,
				idx2: idx2,
				[CSRF_TOKEN_NAME]: "305140a7a37d610be17b7d3d7f3babd66823af784e2b6b20f2a03165997fcc55"			}
		});
	}

	/**
	 * Add object to the list of favorites.
	 */
	function add2favorites(object, objectid) {
		sendAjaxData('zabbix.php?action=favorite.create', {
			data: {
				object: object,
				objectid: objectid,
				[CSRF_TOKEN_NAME]: "902bfeb4a5498b0aaf54236c4eb5df617965a90a7d60e963704c19cd3375de15"			}
		});
	}

	/**
	 * Remove object from the list of favorites. Remove all favorites if objectid==0.
	 */
	function rm4favorites(object, objectid) {
		sendAjaxData('zabbix.php?action=favorite.delete', {
			data: {
				object: object,
				objectid: objectid,
				[CSRF_TOKEN_NAME]: "902bfeb4a5498b0aaf54236c4eb5df617965a90a7d60e963704c19cd3375de15"			}
		});
	}
</script>
<script type="text/javascript">
jQuery("#filter_slaid").multiSelect();
jQuery("#filter_serviceid").multiSelect();
</script></div>
```