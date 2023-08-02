# ScorchedEarth
backend:
    spot reserve -> how is the time fetched ? nf

    subscribe -> need front end for this, how is duration recived? nf

    modify slots table whenever we checkin or checkout -> done

    secure form submissions to only post -> done, bad method requests will take to a page 

    make the starting value of parking id 1000 -> i think not possible natively on sqlite -> if first value is 1000, then it will create the following rows from 1001, should i insert  empty row for this?, or i could make the check if its the first row, then we will insert 1000 explicitly... but we would be checking the table size everytime... dont like it -> better to insert  row with 1000 and then immediately delete it lmao-> didnt work not worth to pursue, just let it be 1

    members get a guaranteed spot, so members cannot be more than the available slots.....
    dang need another endpoint now, should be public -> done


    create a table to store subscription costs
    ARRANGE THE END POINTS SUCH THAT THEY ARE IN SOME KIND OF ORDER -> last priority

frontend:
    admin login -> done 
    admin signup -> should only be visible in the admin login page
    
    in index.html, the two forms should have the same height, make the user checkin form height that of guest

    username can only be a string and not a number, atleast the first char should not be a number

    refresh button to available slots in user dashboard
****************************************************************************
DO THE BELOW ASAP
    IN index.html SHOW THE AVAILABLE SPOTS IN THE MIDDLE COLUMN, THE MESSAGES OF SUCCESSFULL CHECKINS ETC SHOULD COME BELOW IT 
        '/fetchAvailableSlots' -> use this end point end point, should be a post request
    IF AVAILBLE_SLOTS  == zero GREY OUT CHECKINS.....
****************************************************************************

signup bonus of 50 for new users-> done

pre park and create some rows in each table while submitting