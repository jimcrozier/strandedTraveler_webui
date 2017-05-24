function pt(lon, lat) {
    return new kartograph.LonLat(lon, lat);
}
function pad(str, max) {
  str = str.toString();
  return str.length < max ? pad("0" + str, max) : str;
}
function addRoutesToMap(map, pairs) {
    for (var i=0;i<pairs.length;i++) {
        record = pairs[i];
        airport1 = pt(record['airport_1_lon'],record['airport_1_lat']);
        airport2 = pt(record['airport_2_lon'],record['airport_2_lat']);
        classes = record['map_key'] + " route";
        map.addGeoPath([airport1,airport2],[],classes);
    }
}
var language = "en"
function changeLanguage(newLanguage) {
    language = newLanguage;
    $("#settingsMenu li#language li").removeClass("checked");
    $("#settingsMenu li#language li#"+newLanguage).addClass("checked");
}
function addAirportsToMap(map, airports) {
    map.addSymbols({
        type: kartograph.Bubble,
        data: airports,
        location: function(d) { return [d.longitude, d.latitude] },
        radius: function(d) {
            if (d.activity > LARGE_ACTIVITY_THRESHOLD) {
                return 2;
            } else {
                return 1;
            }
        },
        class: function(d) {
            if (d.activity > HUB_ACTIVITY_THRESHOLD) {
                return d.airport + " hub large airportDot";
            } else if (d.activity > LARGE_ACTIVITY_THRESHOLD){
                return d.airport + " large airportDot";
            } else { 
                return d.airport + " airportDot";
            }
        },  
        title: function(d) { return d.airport_name; }     
    });
    map.addSymbols({
        type: kartograph.Label,
        data: airports,
        location: function(d) { return [d.longitude, d.latitude] },
        class: function(d) {
            if (d.activity > HUB_ACTIVITY_THRESHOLD) {
                return d.airport + " hub large airportCode";
            } else if (d.activity > LARGE_ACTIVITY_THRESHOLD){
                return d.airport + " large airportCode";
            } else {
                return d.airport + " airportCode";
            }
        },
        text: function(d) { return d.airport; }  
    });
}
function getIssuesInWindow(issueDate, issueWindow) {
     $.getJSON("/issues", {
         "date": Math.floor(issueDate.getTime()/1000),
         "window": issueWindow,
         "airline_code": customerCode
         
     }, function(issues) {
         for (var i=0;i<issues.length;i++) {
             displayIssue(issues[i]);
         }
     });
}
function mapKeyForAirports(a, b) {
    l = [a, b].sort();
    return l[0] + l[1];
    
}
var allFlights = {};
function displayIssue(issue) {
    $(".noIssuesYet").hide();
    delayTime = issue.departure_delay;
    delayTimeHrs = Math.floor(delayTime/60);
    delayTimeMins = delayTime % 60;
    mapKey = mapKeyForAirports(issue.origin, issue.destination);
    issue.mapKey = mapKey;
    allFlights[issue.flight_number] = issue;
    allFlights[issue.flight_number].offers = [];
    allFlights[issue.flight_number].step = "notStarted";
    allFlights[issue.flight_number].hasShakenIcon = 0;
    flightClass = "fl" + String(issue.flight_number);
    issueHTML = "<a href='#' onclick='toggleIssueDetails("+ String(issue.flight_number) +")' class='list-group-item "+ flightClass +"'>";
    issueHTML += "<h4 class='list-group-item-heading'>"+ customerName + " " + String(issue.flight_number);
    if (!issue.cancelled) {
        issueHTML += "<span class='label label-warning'>Delayed "+ String(delayTimeHrs) +"h"+ String(delayTimeMins) +"m</span>";
        $(".route."+mapKey).addClass("delayed");
        $(".route."+mapKey).each(function() {$(this).parent().append(this);});
        if (issue.carrier_delay >= 60) {
            allFlights[issue.flight_number].causedBy = customerName;
        } else {
            allFlights[issue.flight_number].causedBy = "Weather";
        }
    } else {
        allFlights[issue.flight_number].causedBy = customerName;
        issueHTML += "<span class='label label-danger'>Cancelled</span>";
        $(".route."+mapKey).addClass("cancelled");
        $(".route."+mapKey).each(function() {$(this).parent().append(this);});
    }
    issueHTML += "</h4>";
    issueHTML += "<p class='list-group-item-text'>" + issue.origin + " &#9656; " + issue.destination + "<br />"+issue.model.trim()+", " + String(issue.passengers_affected) + " passengers</p></a>";
    $(issueHTML).prependTo("#sidebar .list-group").hide().slideDown();
}
var currentFlightNumber = -1;
function toggleIssueDetails(flightNumber) {
    flight = allFlights[flightNumber];
    if (currentFlightNumber == flightNumber) {
        hideIssueDetails();
    } else {
        showIssueDetails(flightNumber);
    }
}
function showIssueDetails(flightNumber) {
    $(".list-group-item.fl"+currentFlightNumber).removeClass("active");
    $(".list-group-item.fl"+flightNumber).addClass("active");
    currentFlightNumber = flightNumber;
    flight = allFlights[flightNumber];
    $(".route").fadeOut();
    $(".airportDot").fadeOut();
    $(".airportCode").fadeOut();
    airportDotSel = ".airportDot." + flight.origin + ", .airportDot." + flight.destination;
    airportCodeSel = ".airportCode." + flight.origin + ", .airportCode." + flight.destination;
    $(airportDotSel).fadeIn();
    $(airportCodeSel).fadeIn();
    $(".route."+flight.mapKey).fadeIn();
    $(".noSelection").hide();   
    $(".issueSelected").fadeIn();
    
    $(".detailTitle").html(customerName + " " + String(flight.flight_number));
    if (!flight.cancelled) {
        delayTime = flight.departure_delay;
        delayTimeHrs = Math.floor(delayTime/60);
        delayTimeMins = delayTime % 60;
        $(".detailStatus").html("Delayed "+ String(delayTimeHrs) +"h"+ String(delayTimeMins) +"m");
        $(".detailStatus").addClass("label-warning");
        $(".detailStatus").removeClass("label-danger");
        tempDate = new Date(flight.scheduled_departure_local);
        tempTime = new Date(((tempDate.getTime()/60000) + flight.departure_delay)*60000);
        $(".detailActualDeparture").html(String(tempTime.getHours())+":"+pad(String(tempTime.getMinutes()), 2));
    } else {
        $(".detailStatus").html("Cancelled");
        $(".detailStatus").addClass("label-danger");
        $(".detailStatus").removeClass("label-warning"); 
        $(".detailActualDeparture").html("N/A");       
    }
    $(".detailOrigin").html(flight.origin);
    $(".detailDestination").html(flight.destination);
    tempTime = new Date(flight.scheduled_departure_local); 
    $(".detailScheduledDeparture").html(String(tempTime.getHours())+":"+pad(String(tempTime.getMinutes()), 2));
    $(".detailDelayReason").html(flight.causedBy);
    $(".detailCustomersMiss").html(String(flight.passengers_affected));
    $("#progressMessage").hide();
    $("#doneMessage").hide();
    $("#mobileAppIconBox button").attr('disabled', true);
    $(".unreadNotifications").hide();
    if (flight.step == "requestedOffers") {
        $("#progressMessage").show();
    } else if (flight.step == "haveOffers") {
        $(".offerCount").html(String(flight.offers.length));
        $("#doneMessage").show();
        if (flight.hasShakenIcon == 0) {
            flight.hasShakenIcon = 1;
            $("#mobileAppIconWrapper").effect("shake", {distance: 5, times:2});            
        }
        $("#mobileAppIconBox button").attr('disabled', false);
        $(".unreadNotifications").fadeIn();
    }
     
        
    
}
function hideIssueDetails() {
    if (currentFlightNumber == -1) {
        return;
    }
    $(".list-group-item.fl"+currentFlightNumber).removeClass("active");
    currentFlightNumber = -1;
    $(".route").fadeIn();
    $(".airportDot").fadeIn();
    $(".airportCode").fadeOut();
    $(".airportCode.large").fadeIn();
    $(".issueSelected").hide();
    $(".noSelection").fadeIn(); 
    $("#progressMessage").hide();
    $("#doneMessage").hide();
    $(".unreadNotifications").hide();
    $("#mobileAppIconBox button").attr('disabled', true);
}
function createOffers() {
    allFlights[currentFlightNumber].step = "requestedOffers";
    $("#progressMessage").fadeIn();
    requestOffers(currentFlightNumber);
}
// Code to handle playing back historical flight events
var playbackEnabled = false;
var playbackTimer = 0;
var startFlightCount = 0;
function startPlayback() {
    var stepBaseMs = 1000;
    var stepPlaybackMs = stepBaseMs*playbackSpeed;
    playbackEnabled = true;
    startFlightCount = Object.keys(allFlights).length;
    playbackTimer = setTimeout(function(){_playback(stepBaseMs, stepPlaybackMs)}, stepBaseMs);
}
function _playback(stepBaseMs, stepPlaybackMs) {
    playbackDate = new Date(playbackDate.getTime() + stepPlaybackMs);
    getIssuesInWindow(playbackDate, (stepPlaybackMs/1000));
    playbackTimer = setTimeout(function(){_playback(stepBaseMs, stepPlaybackMs)}, stepBaseMs);
    //stop every 25 flights
    if (Object.keys(allFlights).length >= startFlightCount + 25) {
        togglePlayback();        
    }
}
function stopPlayback() {
    playbackEnabled = false;
    clearTimeout(playbackTimer);
}
function togglePlayback() {
    if (playbackEnabled) {
        $("#playbackButton span.glyphicon").removeClass("glyphicon-pause");
        $("#playbackButton span.glyphicon").addClass("glyphicon-play");
        stopPlayback();
    } else {
        $("#playbackButton span.glyphicon").removeClass("glyphicon-play"); 
        $("#playbackButton span.glyphicon").addClass("glyphicon-pause");
        startPlayback(playbackDate, playbackSpeed);       
    }
}