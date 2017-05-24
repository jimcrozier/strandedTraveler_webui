function requestOffers(flight_number) {
    flight = allFlights[flight_number];
    d = new Date(flight.scheduled_departure_local);
    msg = { "flightAirlineCode" : customerCode, "flightNumber" : flight_number, "flightDate" : d.toISOString().slice(0, 10) };
    $.getJSON("/spark-talker", {
        "message": JSON.stringify(msg),        
    });    
    checkForOffers(flight_number);
}
function checkForOffers(flight_number) {
    flight = allFlights[flight_number];
    d = new Date(flight.scheduled_departure_local);
    $.getJSON("/offers", {
        "date": Math.floor(d.getTime()/1000),
        "flight_number": flight.flight_number,
        "airline_code": customerCode,
        "is_generic": isGeneric
        
    }, function(results) {
        if (results.length == 0) {
            console.log("No offers present for flight " + String(flight_number) + ". Checking again in 3s.")
            allFlights[flight_number].offerCheckTimer = setTimeout(function(){checkForOffers(flight_number)}, 3000);
        } else {            
            if (allFlights[flight_number].offers.length==results.length) {
                allFlights[flight_number].noChanges += 1;
                if (allFlights[flight_number].noChanges == 6) {
                    clearTimeout(allFlights[flight_number].offerCheckTimer);
                }
                return
            }
            allFlights[flight_number].step = "haveOffers";
            allFlights[flight_number].noChanges = 0;
            allFlights[flight_number].offers = results;
            if (results.length > allFlights[flight_number].passengers_affected) {
                            allFlights[flight_number].offers = results.slice(0, allFlights[flight_number].passengers_affected);
            }
            showIssueDetails(flight_number);
            if (currentPassengerIndex != -1) {
                displayPassenger(currentPassengerIndex);
            }
            allFlights[flight_number].offerCheckTimer = setTimeout(function(){checkForOffers(flight_number)}, 3000);
        }
        
    });    
}
var currentPassengerIndex = -1;
function displayPassenger(passengerIndex) {
    flight=allFlights[currentFlightNumber];
    offers = flight.offers;
    offer = offers[passengerIndex];
    d = new Date(flight.scheduled_departure_local);
    if (currentPassengerIndex != passengerIndex) {
        $.getJSON("/setCurrentPassengerBeingViewed", {
            "date": Math.floor(d.getTime()/1000),
            "flight_number": flight.flight_number,
            "airline_code": customerCode,
            "passenger_id": offer.passengerId
        }, function(results) {
            newURL = iframeURL + offer.passengerExceptionId;
            newURL = newURL.replace('replaceWithLanguage', language);
            newURL += "?isGeneric=" + String(isGeneric);
            $( '#customerDeviceView' ).attr( 'src', newURL);
            
        }); 
        
    }
    currentPassengerIndex = passengerIndex;
    
    $("#customerViewNav #customerText").html("Passenger " + String(passengerIndex+1) + " of " + String(offers.length));    
    $("table#customerDocument tbody").html("");
    
    for (var key in offer) {
        var row = $("<tr></tr>").appendTo("table#customerDocument tbody");
        row.append("<td>" + String(key) + "</td>");
        row.append("<td>" + String(offer[key]) + "</td>");
    }
    if (passengerIndex==0){
        $("#customerView .previousButton").attr("disabled", true);
    } else {
        $("#customerView .previousButton").attr("disabled", false);
        var act = "displayPassenger(" + String(passengerIndex-1) + ")";
        $("#customerView .previousButton").attr("onclick", act);
    }
    if (passengerIndex==(offers.length-1)){
        $("#customerView .nextButton").attr("disabled", true);
    } else {
        $("#customerView .nextButton").attr("disabled", false);
        var act2 = "displayPassenger(" + String(passengerIndex+1) + ")";
        $("#customerView .nextButton").attr("onclick", act2);
    }

}