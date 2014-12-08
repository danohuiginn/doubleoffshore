---
layout: page
title: Viz
permalink: /viz/
---
<div ng-controller="NetworkController as network" class="container-fluid">
    <!-- network canvas -->
    <div id="canvas" class="col-md-5"></div>

    <!-- map view -->
    <div id="map" class="col-md-5">
    </div>

    <!-- query controls -->
    <div class="pull-right col-md-2">
        <form ng-submit="network.createNetwork()">
            Show me rigs<br />in
            <select ng-model="currentLocation" ng-options="country for (country, rigs) in locations">
                <option value="">any country</option>
            </select>
            <br />that are owned by
            <select ng-model="currentCompany" ng-options="company for (company, rigs) in companies">
                <option value="">anyone</option>
            </select>
            <br />and sailing under
            <select ng-model="currentFlag" ng-options="flag for (flag, rigs) in flags">
                <option value="">any country</option>
            </select>
            <br/><input type="submit" class="btn btn-default" value="Show rigs" />
        </form>

        <button ng-click="network.groupByLocation()" class="group-by btn btn-default">Group by rig location</button>
        <button ng-click="network.groupByFlags()" class="group-by btn btn-default">Group by rig flag</button>
    </div>
</div>

<script type="text/javascript" src="{{ "/assets/js/jquery/jquery.min.js" | prepend: site.baseurl }}"></script>
<script type="text/javascript" src="{{ "/assets/js/angular/angular.min.js" | prepend: site.baseurl }}"></script>
<script type="text/javascript" src="{{ "/assets/js/d3/d3.min.js" | prepend: site.baseurl }}"></script>
<script type="text/javascript" src="{{ "/assets/js/d3-geo-projection/index.js" | prepend: site.baseurl }}"></script>
<script type="text/javascript" src="{{ "/assets/js/topojson/topojson.js" | prepend: site.baseurl }}"></script>
<script type="text/javascript" src="{{ "/assets/js/webcola/cola.v3.min.js" | prepend: site.baseurl }}"></script>
<script type="text/javascript" src="{{ "/assets/js/app.js" | prepend: site.baseurl }}"></script>

<style>
    /* Network style */

    .relation {
        stroke: #ECD078;
        stroke-width: 2px;
    }

    .relation-manager {stroke: #D95B43;}
    .relation-operator {stroke: #542437;}
    .entity-rig {fill: #53777A;}
    .entity-company {fill: #C02942;}

    /* Widgets style */

    text.label {fill: white;}

    .btn {margin-top: 8px;}

    /* Map style */

    .graticule {
      fill: none;
      stroke: #777;
      stroke-width: .5px;
      stroke-opacity: .5;
    }

    .land {
      fill: #222;
    }

    .boundary {
      fill: none;
      stroke: #fff;
      stroke-width: .5px;
    }
</style>