package ch.puhl.wienaktuell;



public class DelegationService extends
        com.google.androidbrowserhelper.trusted.DelegationService {
    @Override
    public void onCreate() {
        super.onCreate();
        /* Standort für die Web-App: Chrome fragt ihn bei der App an, weil sie Standortrechte hat (Widget) */
        registerExtraCommandHandler(
                new com.google.androidbrowserhelper.locationdelegation.LocationDelegationExtraCommandHandler());

        
    }
}

