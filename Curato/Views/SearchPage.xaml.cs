using System.Windows.Controls;
using Curato.ViewModels;

public partial class SearchPage : UserControl
{
    public SearchPage()
    {
        InitializeComponent();
        this.DataContext = new InputViewModel();
    }
}
