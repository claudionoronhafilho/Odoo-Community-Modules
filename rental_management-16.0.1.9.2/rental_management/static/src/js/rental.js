odoo.define('rental_management.PropertyDashboard', function (require) {
  'use strict';
  const AbstractAction = require('web.AbstractAction');
  const ajax = require('web.ajax');
  const core = require('web.core');
  const rpc = require('web.rpc');
  const session = require('web.session')
  const web_client = require('web.web_client');
  const _t = core._t;
  const QWeb = core.qweb;
  const ActionMenu = AbstractAction.extend({
    template: 'rentalDashboard',
    events: {
      'click .avail-property': 'view_avail_property',
      'click .total-property': 'view_total_property',
      'click .booked-property': 'view_booked_property',
      'click .lease-property': 'view_lease_stats',
      'click .sale-property': 'view_sale_stats',
      'click .sold-property': 'view_sold_stats',
      'click .sold-total': 'view_property_sold',
      'click .rent-total': 'view_property_rent',
      'click .draft-contract': 'view_draft_rent',
      'click .running-contract': 'view_running_rent',
      'click .expire-contract': 'view_expire_rent',
      'click .booked-property-sale': 'view_booked_sale',
      'click .sale-sold': 'view_sale_sold',
      'click .pending-invoice': 'view_pending_invoice',
    },
    renderElement: function (ev) {
      const self = this;
      $.when(this._super())
        .then(function (ev) {
          rpc.query({
            model: "property.details",
            method: "get_property_stats",
          }).then(function (result) {
            $('#avail_property').empty().append(result['avail_property']);
            $('#booked_property').empty().append(result['booked_property']);
            $('#lease_property').empty().append(result['lease_property']);
            $('#sale_property').empty().append(result['sale_property']);
            $('#sold_property').empty().append(result['sold_property']);
            $('#total_property').empty().append(result['total_property']);
            $('#sold_total').empty().append(result['sold_total']);
            $('#rent_total').empty().append(result['rent_total']);
            $('#draft_contract').empty().append(result['draft_contract']);
            $('#running_contract').empty().append(result['running_contract']);
            $('#expire_contract').empty().append(result['expire_contract']);
            $('#booked').empty().append(result['booked']);
            $('#sale_sold').empty().append(result['sale_sold']);
            $('#pending_invoice').empty().append(result['pending_invoice']);
            self.propertyType(result['property_type']);
            self.propertyStages(result['property_stage']);
            self.topBrokers(result['tenancy_top_broker']);
            self.topBrokersSold(result['tenancy_top_broker']);
            self.tenancyDuePaid(result['due_paid_amount']);
            self.soldDuePaid(result['due_paid_amount']);
          });
        });
    },
    view_avail_property: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Available Property'),
        type: 'ir.actions.act_window',
        res_model: 'property.details',
        domain: [['stage', '=', 'available']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_total_property: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Total Property'),
        type: 'ir.actions.act_window',
        res_model: 'property.details',
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_booked_property: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Booked Property'),
        type: 'ir.actions.act_window',
        res_model: 'property.details',
        domain: [['stage', '=', 'booked']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_lease_stats: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Property On Lease'),
        type: 'ir.actions.act_window',
        res_model: 'property.details',
        domain: [['stage', '=', 'on_lease']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_sale_stats: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Property On Sale'),
        type: 'ir.actions.act_window',
        res_model: 'property.details',
        domain: [['stage', '=', 'sale']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_sold_stats: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Sold Property'),
        type: 'ir.actions.act_window',
        res_model: 'property.details',
        domain: [['stage', '=', 'sold']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_property_sold: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Property Sold'),
        type: 'ir.actions.act_window',
        res_model: 'property.vendor',
        domain: [['stage', '=', 'sold']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_property_rent: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Property Rent'),
        type: 'ir.actions.act_window',
        res_model: 'rent.invoice',
        domain: ['|', ['type', '=', 'rent'], ['type', '=', 'full_rent']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_draft_rent: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Draft Contract'),
        type: 'ir.actions.act_window',
        res_model: 'tenancy.details',
        domain: [['contract_type', '=', 'new_contract']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_running_rent: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Running Contract'),
        type: 'ir.actions.act_window',
        res_model: 'tenancy.details',
        domain: [['contract_type', '=', 'running_contract']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_expire_rent: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Expire Contract'),
        type: 'ir.actions.act_window',
        res_model: 'tenancy.details',
        domain: [['contract_type', '=', 'expire_contract']],
        views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_booked_sale: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Booked Property'),
        type: 'ir.actions.act_window',
        res_model: 'property.vendor',
        domain: [['stage', '=', 'booked']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_sale_sold: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Sold Property'),
        type: 'ir.actions.act_window',
        res_model: 'property.vendor',
        domain: [['stage', '=', 'sold']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
     view_pending_invoice: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Pending Invoice'),
        type: 'ir.actions.act_window',
        res_model: 'rent.invoice',
        domain: [['payment_state', '=', 'not_paid']],
        views: [[false, 'list'], [false, 'form'], [false, 'search']],
        context:{'search_default_landlord':1},
        target: 'current'
      });
    },
    get_action: function (ev, name, res_model) {
      ev.preventDefault();
      return this.do_action({
        name: _t(name),
        type: 'ir.actions.act_window',
        res_model: res_model,
        views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
        target: 'current'
      });
    },
    apexGraph: function () {
      Apex.grid = {
        padding: {
          right: 0,
          left: 0,
          top: 10,
        }
      }
      Apex.dataLabels = {
        enabled: false
      }
    },
    //Graph
    propertyType: function (data) {
      const options = {
        series: data[1],
        chart: {
          type: 'donut',
          height: 410
        },
        colors: ['#33679c', '#6FFCD0', '#F084A3', '#82CDFF'],
        dataLabels: {
          enabled: false
        },
        labels: data['0'],
        legend: {
          position: 'bottom',
        },
      };
      this.renderGraph("#property_type", options);
    },
    propertyStages: function (data) {
      const options = {
        series: data[1],
        chart: {
          type: 'pie',
          height: 410
        },
        colors: ['#FFADAD', '#FFD6A5', '#FDFFB6', '#CAFFBF', '9BF6FF'],
        dataLabels: {
          enabled: false
        },
        labels: data[0],
        legend: {
          position: 'bottom',
        },

      };
      this.renderGraph("#property_stages", options);
    },
    topBrokers: function (data) {
      var options = {
        series: [{
          name: "Tenancies",
          data: data[1],
        }],
        chart: {
          height: 350,
          type: 'bar',
        },
        colors: ['#FFADAD', '#FFD6A5', '#FDFFB6', '#CAFFBF', '9BF6FF'],
        plotOptions: {
          bar: {
            columnWidth: '45%',
            distributed: true,
          }
        },
        dataLabels: {
          enabled: false
        },
        legend: {
          show: false
        },
        xaxis: {
          categories: data[0],
          labels: {
            style: {
              fontSize: '12px'
            }
          }
        }
      };
      this.renderGraph("#top_brokers", options);
    },
    topBrokersSold: function (data) {
      var options = {
        series: [{
          name: "Property Sale",
          data: data[3],
        }],
        chart: {
          height: 350,
          type: 'bar',
        },
        colors: ['#FFADAD', '#FFD6A5', '#FDFFB6', '#CAFFBF', '9BF6FF'],
        plotOptions: {
          bar: {
            columnWidth: '45%',
            distributed: true,
          }
        },
        dataLabels: {
          enabled: false
        },
        legend: {
          show: false
        },
        xaxis: {
          categories: data[2],
          labels: {
            style: {
              fontSize: '12px'
            }
          }
        }
      };
      this.renderGraph("#top_brokers_sale", options);
    },
    tenancyDuePaid: function (data) {
      const options = {
        series: data[3],
        chart: {
          type: 'pie',
          height: 410
        },
        colors: ['#FF6464', '#96BB7C'],
        dataLabels: {
          enabled: false
        },
        labels: data[2],
        legend: {
          position: 'bottom',
        },
      };
      this.renderGraph("#tenancy_due_paid", options);
    },
    soldDuePaid: function (data) {
      const options = {
        series: data[1],
        chart: {
          type: 'pie',
          height: 410
        },
        colors: ['#FF1700', '#4AA96C'],
        dataLabels: {
          enabled: false
        },
        labels: data[0],
        legend: {
          position: 'bottom',
        },
      };
      this.renderGraph("#sold_due_paid", options);
    },
    renderGraph: function (render_id, options) {
      $(render_id).empty();
      const graphData = new ApexCharts(document.querySelector(render_id), options);
      graphData.render();
    },
    willStart: function () {
          const self = this;
            return this._super()
            .then(function() {});
    },
  });
  core.action_registry.add('property_dashboard', ActionMenu);
});
