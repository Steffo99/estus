function delet(base_url, id, name)
{
    if(confirm("Sei sicuro di voler eliminare " + name + "? Non potrai annullare l'operazione una volta eseguita!"))
        window.location.href = base_url.replace("12341234", id);
}