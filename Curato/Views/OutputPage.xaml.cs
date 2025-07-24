using System.Windows.Controls;


namespace Curato.Views
{
    public partial class OutputPage : UserControl
    {
        public OutputPage()
        {
            InitializeComponent();
            this.DataContext = AppState.SharedInputViewModel;
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            var mainWindow = Window.GetWindow(this) as MainWindow;
            if (mainWindow != null)
            {
                mainWindow.MainFrame.Content = new SearchPage();
            }
        }
    }
}


